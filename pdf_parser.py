#!/usr/bin/python
# coding: utf-8

import logging
import os
import re
import traceback
from binascii import b2a_hex
from operator import itemgetter
from xml.sax.saxutils import escape

import lxml.etree
from lxml import etree
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage, LTTextLineHorizontal, LTChar, LTCurve
from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser


class Pdf2xml:

    def __init__(self, file):
        self.file = file
        self.rsrcmgr = PDFResourceManager()
        self.laparams = LAParams()
        self.device = PDFPageAggregator(self.rsrcmgr, laparams=self.laparams)
        self.interpreter = PDFPageInterpreter(self.rsrcmgr, self.device)

    def run(self):
        xml = self.parse()
        xml = etree.ElementTree(xml)
        with open(os.path.basename(self.file).replace(".pdf", "") + ".xml", 'wb') as f:
            xml.write(f, encoding="utf-8", xml_declaration=True, pretty_print=True)

    def parse(self):
        if self.file is None:
            logging.error('pdf2xml: File is not set')
            raise Exception('pdf2xml: File is not set')
        try:
            new_xml = self.create_xml()
            xml = lxml.etree.fromstring(new_xml)
            if len(xml.xpath('//text')) == 0:
                xml = lxml.etree.fromstring("<doc></doc>")
        except BaseException:
            print(traceback.format_exc())
            xml = lxml.etree.fromstring("<doc></doc>")
            logging.error("pdf2xml->parse->try lxml.fromstring")
        return xml

    @staticmethod
    def parse_page_xml(fileobj):
        pdfxml = fileobj.read()
        root = lxml.etree.fromstring(pdfxml)
        rows = []
        pages = []
        for pagenum, page in enumerate(root):
            assert page.tag == 'page'
            pagelines = {}
            for v in page:
                if v.tag == 'text':
                    # there has to be a better way here to get the contents
                    text = re.match('(?s)<text.*?>(.*?)</text>', lxml.etree.tostring(v)).group(1)
                    if not text.strip():
                        continue
                    left = int(v.attrib.get('left'))
                    top = int(v.attrib.get('top'))

                    # fix some off-by-one placement issues,
                    # which make some text span over two lines where it should be in one
                    if top - 1 in pagelines:
                        top = top - 1
                    elif top + 1 in pagelines:
                        top = top + 1
                    line = pagelines.setdefault(top, [])
                    line.append((left, text))

            ordered = list(sorted([(k, sorted(v)) for k, v in pagelines.items()]))
            rows.extend(ordered)
            pages.append((pagenum, ordered))
        return pages

    @staticmethod
    def with_pdf(pdf_doc, fn, *args):
        """Open the pdf document, and apply the function, returning the results"""
        result = None
        try:
            # open the pdf file
            if hasattr(pdf_doc, 'read'):
                fp = pdf_doc
            else:
                fp = open(pdf_doc, 'rb')
            # create a parsers object associated with the file object
            parser = PDFParser(fp)
            # create a PDFDocument object that stores the document structure
            doc = PDFDocument(parser)
            # connect the parsers and document objects
            parser.set_document(doc)
            # supply the password for initialization
            # doc.initialize(pdf_pwd)

            if doc.is_extractable:
                # apply the function and return the result
                result = fn(doc, *args)

            # close the pdf file
            fp.close()
        except IOError:
            # the file doesn't exist or similar problem
            pass
            raise
        return result

    @staticmethod
    def parse_toc(doc):
        """With an open PDFDocument object, get the table of contents (toc) data
        [this is a higher-order function to be passed to with_pdf()]"""
        toc = []
        try:
            outlines = doc.get_outlines()
            for (level, title, dest, a, se) in outlines:
                toc.append((level, title))
        except PDFNoOutlines:
            pass
        return toc

    def get_toc(self, pdf_doc):
        """Return the table of contents (toc), if any, for this pdf file"""
        return self.with_pdf(pdf_doc, self.parse_toc)

    def _parse_pages(self, doc, image_handler):
        """With an open PDFDocument object, get the pages, parse each one, and return the entire text
        [this is a higher-order function to be passed to with_pdf()]"""
        text_content = ['<document>']  # a list of strings, each representing text collected from each page of the doc
        for i, page in enumerate(PDFPage.create_pages(doc)):
            text_content.append(
                '<page number="%s" width="%s" height="%s">' % (i + 1, page.mediabox[2], page.mediabox[3]))
            self.interpreter.process_page(page)
            # receive the LTPage object for this page
            layout = self.device.get_result()
            page_height = int(layout.bbox[3])
            # layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.
            ret = self.parse_lt_objs(layout._objs, (i + 1), image_handler, page_height)
            text_content.append(ret)
            text_content.append('</page>')

        text_content.append('</document>')
        return text_content

    def get_pages(self, pdf_doc, image_handler=None):
        """Process each of the pages in this pdf file and print the entire text to stdout"""
        return self.with_pdf(pdf_doc, self._parse_pages, *tuple([image_handler]))

    @staticmethod
    def is_on_same_row(char, row):
        return row[0] <= char.bbox[1] <= row[1]

    @staticmethod
    def is_near_by_last_string(char, prew_char):
        return char.bbox[0] <= prew_char[2] + 10

    @staticmethod
    def is_between_numbers(position, chars):
        if 1 <= position < len(chars) - 1:
            return (chars[position - 1].get_text().isdigit() or chars[position - 1].get_text() in ('+', '-')) \
                   and chars[position + 1].get_text().isdigit()
        return False

    @staticmethod
    def replace_ascii_code(char) -> str:
        if 'cid' in char.lower():
            text_str = char.lower()
            text_str = text_str.strip('(')
            text_str = text_str.strip(')')
            ascii_num = text_str.split(':')[-1]
            ascii_num = int(ascii_num)
            return chr(ascii_num)
        else:
            return char

    def create_words_from_chars(self, chars: []):
        special_char = False
        words = {}
        row = []
        end_position = None
        start_position = None
        prew_char = []
        word = ""
        is_word = 0
        i = 0

        for char in chars:
            if not isinstance(char, LTChar):
                i += 1
                continue

            if special_char:
                special_char = False
                i += 1
                continue
            # if char.get_text() in self.config.get_array("pdf2xml_parser", "illegal_characters"):
            #     i += 1
            #     continue
            # if char.get_text() in self.config.get_array("pdf2xml_parser",
            #                                             "number_separators") and self.is_between_numbers(i, chars):
            #     prew_char = char.bbox
            #     i += 1
            #     continue

            is_between_number = self.is_between_numbers(i, chars)

            if char.get_text() == '?':
                start_position = char.bbox
                word += "fi"
                special_char = True
                i += 1
                continue

            if len(prew_char) > 0 and is_word == 1 and not self.is_near_by_last_string(char, prew_char) \
                    and not is_between_number:
                if is_word == 1:
                    words = self.add_words(start_position, end_position, word, words)
                    end_position = None
                    is_word = 0

            if len(row) > 0 and not self.is_on_same_row(char, row) or \
                    len(prew_char) > 0 and not self.is_near_by_last_string(char, prew_char) \
                    and not is_between_number:
                if is_word == 1:
                    words = self.add_words(start_position, end_position, word, words)
                    end_position = None
                    is_word = 0

            if char.get_text() == " " or char.get_text() == "?":
                if is_word == 1:
                    words = self.add_words(start_position, end_position, word, words)
                    end_position = None
                    is_word = 0

                i += 1
                continue

            text_val = self.replace_ascii_code(char.get_text())
            if is_word == 0:
                row.insert(0, int(char.bbox[1]))
                row.insert(1, int(char.bbox[3]))
                is_word = 1
                word = text_val
                start_position = char.bbox
                prew_char = char.bbox

            else:
                word += text_val
                end_position = char.bbox
                prew_char = char.bbox
            i += 1

        if is_word == 1:
            words = self.add_words(start_position, end_position, word, words)
            end_position = None

        return words

    @staticmethod
    def return_utf(s):
        if isinstance(s, str):
            return s.encode('utf-8', errors='replace')
        if isinstance(s, (int, float, complex)):
            return str(s).encode('utf-8')
        try:
            return s.encode('utf-8')
        except TypeError:
            try:
                return str(s).encode('utf-8')
            except AttributeError:
                return s
        except AttributeError:
            return s

    def parse_image(self):
        pass

    def parse_lt_objs(self, lt_objs, page_number, image_handler, page_height, text=None):
        """Iterate through the list of LT* objects and capture the text or image data contained in each"""
        # images_folder = 'storage/task_data/images/'

        if text is None:
            text = []
        text_content = []
        chars = []
        page_text = {}  # k=(x0, x1) of the bbox, v=list of text strings within that bbox width (physical column)
        for lt_obj in lt_objs:
            if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine) \
                    or isinstance(lt_obj, LTTextLineHorizontal):
                # text, so arrange is logically based on its column width
                page_text = self.update_page_text_hash(page_text, lt_obj)

            # elif isinstance(lt_obj, LTImage):
            #     try:
            #         os.mkdir(images_folder)
            #     except FileExistsError:
            #         pass
            #
            #     saved_file = self.save_image(lt_obj, page_number, images_folder)
            #     if saved_file:
            #         text_content.append('<img src="' + os.path.join(images_folder, saved_file) + '" />')
            #     else:
            #         import sys
            #         print(sys.stderr, "Error saving image on page", page_number, lt_obj.__repr__)

            elif isinstance(lt_obj, LTFigure):
                # LTFigure objects are containers for other LT* objects, so recurse through the children
                text_content.append(
                    self.parse_lt_objs(lt_obj._objs, page_number, image_handler, page_height, text_content))
            elif isinstance(lt_obj, LTChar):
                chars.append(lt_obj)
        if len(chars) > 0:
            page_text = self.create_words_from_chars(chars)

        page_text_items = [(k[0], k[1], k, v) for k, v in page_text.items()]

        page_text_items = list(sorted(sorted(page_text_items, key=itemgetter(0)), key=itemgetter(1), reverse=True))
        sorted_text = [(c, d) for a, b, c, d in page_text_items]

        for k, v in sorted_text:
            # sort the page_text hash by the keys (x0,x1 values of the bbox),
            # which produces a top-down, left-to-right sequence of related columns
            a = k
            pos = 'top="%s" left="%s" width="%s" height="%s"' % (
                page_height - int(a[1]), int(a[0]), int(a[2] - a[0]), int(a[3] - a[1]))
            text_content.append('<text %s>%s</text>' % (pos, escape(v)))

        return '\n'.join(text_content)

    @staticmethod
    def should_combine(d, i):
        try:
            int(d["text"][i])
        except ValueError:
            return False
        try:
            int(d["text"][i + 1])
        except (ValueError, IndexError):
            return False
        return d['left'][i] + d['width'][i] * 2 > d['left'][i + 1]

    @staticmethod
    def to_bytestring(s, enc='utf-8'):
        """Convert the given unicode string to a bytestring, using the standard encoding,
        unless it's already a bytestring"""
        if s:
            if isinstance(s, str):
                return s
            else:
                return s.encode(enc)

    def get_words_from_chars(self, chars, words):
        for obj in self.create_words_from_chars(chars):
            words = {**words, **self.split_line_to_words(obj)}
        return words

    def split_line_to_words(self, line: [LTTextLineHorizontal, LTTextLine, LTTextBox]):
        chars = []
        for item in line._objs:
            if isinstance(item, LTChar):
                chars.append(item)
        return self.create_words_from_chars(chars)

    @staticmethod
    def add_words(start_position, end_position, word, words):
        left = int(start_position[0])
        top = int(start_position[1])

        if end_position is not None:
            width = int(end_position[2])
            height = int(end_position[3])
        else:
            width = int(start_position[2])
            height = int(start_position[3])

        position = (left, top, width, height)
        words[position] = word
        return words

    def get_lt_type(self, objects, file_content):
        for lt_obj in objects._objs:
            if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine) \
                    or isinstance(lt_obj, LTTextLineHorizontal):
                file_content.append("text")
            elif isinstance(lt_obj, LTImage):
                height, width = lt_obj.srcsize
                if int(height) > 1000 and int(width) > 1000:
                    file_content.append("image")
            elif isinstance(lt_obj, LTCurve):
                file_content.append("curve")
            elif isinstance(lt_obj, LTFigure):
                # LTFigure objects are containers for other LT* objects, so recurse through the children
                self.get_lt_type(lt_obj, file_content)
            else:
                file_content.append("other")
        return file_content

    def detect_type(self):
        file_content_type = []
        for pageNumber, page in enumerate(PDFPage.get_pages(open(self.file, 'rb'))):
            self.interpreter.process_page(page)
            layout = self.device.get_result()
            file_content_type = file_content_type + self.get_lt_type(layout, file_content_type)

        result_types = {}
        if len(file_content_type):
            result_types = {
                "text": file_content_type.count("text") / len(file_content_type) * 100,
                "curve": file_content_type.count("curve") / len(file_content_type) * 100,
                "image": file_content_type.count("image") / len(file_content_type) * 100,
                "other": file_content_type.count("other") / len(file_content_type) * 100
            }
        return result_types

    def update_page_text_hash(self, h, lt_obj, pct=0.2):
        """Use the bbox x0,x1 values within pct% to produce lists of associated text within the hash"""
        # a = lt_obj.bbox
        # print 'left="%s" top="%s" width="%s" height="%s"' % (int(a[0]), int(a[1]), int(a[2]-a[0]), int(a[3]-a[1]))
        for obj in lt_obj._objs:
            h = {**h, **self.split_line_to_words(obj)}
        return h

    def save_image(self, lt_image, page_number, images_folder):
        """Try to save the image data from this LTImage object, and return the file name, if successful"""
        result = None
        if lt_image.stream:
            file_stream = lt_image.stream.get_rawdata()
            file_ext = self.determine_image_type(file_stream[0:4])
            file_name = ''.join([str(page_number), '_', lt_image.name, file_ext])
            if self.write_file(images_folder, file_name, lt_image.stream.get_rawdata(), flags='wb'):
                result = file_name
        return result

    @staticmethod
    def determine_image_type(stream_first_4_bytes):
        """Find out the image file type based on the magic number comparison of the first 4 (or 2) bytes"""
        file_type = ''
        bytes_as_hex = b2a_hex(stream_first_4_bytes)
        if bytes_as_hex.startswith(b'ffd8'):
            file_type = '.jpeg'
        elif bytes_as_hex == '89504e47':
            file_type = '.png'
        elif bytes_as_hex == '47494638':
            file_type = '.gif'
        elif bytes_as_hex.startswith(b'424d'):
            file_type = '.bmp'
        return file_type

    @staticmethod
    def write_file(folder, filename, filedata, flags='w'):
        """Write the file data to the folder and filename combination
        (flags: 'w' for write text, 'wb' for write binary, use 'a' instead of 'w' for append)"""
        result = False
        if os.path.isdir(folder):
            try:
                file_obj = open(os.path.join(folder, filename), flags)
                file_obj.write(filedata)
                file_obj.close()
                result = True
            except IOError:
                pass
        return result

    def pdf2xml_pages(self, fileobj, image_handler=None):
        return self.get_pages(fileobj, image_handler=image_handler)

    def create_xml(self, image_handler=None):
        fileobj = open(self.file, 'rb')
        return ('\n'.join(self.pdf2xml_pages(fileobj, image_handler=image_handler))).lower()


if __name__ == '__main__':
    document_name = "menu_zelenaliska.pdf"
    Pdf2xml(document_name).run()
