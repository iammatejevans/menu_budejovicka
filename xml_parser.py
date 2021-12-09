import xml.etree.ElementTree as ET
from datetime import datetime


class ParseXml:
    def __init__(self, file: str):
        self.file = file
        self.tree = ET.parse(self.file)
        self.results = {}
        self.text_elements = [el for el in self.tree.iter() if el.tag == "text"]

    def run(self):
        pass


class ParseZelenaLiska(ParseXml):
    def run(self):
        if not self.is_today():
            return

        self.soups()
        self.main_courses()

        return self.results

    def is_today(self) -> bool:
        date = False
        for idx, elem in enumerate(self.text_elements):
            if date:
                today = datetime.strftime(datetime.now(), "%-d.%-m")  # change to '-' on linux and '#' on windows
                if elem.text == today:
                    self.update_elements(idx)
                return elem.text == today
            if elem.text in ["pondělí", "úterý", "středa", "čtvrtek", "pátek", "sobota", "neděle"]:
                date = True
                continue
        return False

    def update_elements(self, idx):
        self.text_elements = self.text_elements[idx+1:]

    @staticmethod
    def is_on_one_line(el_one, el_two):
        return abs(int(el_one.attrib.get("top", 0)) - int(el_two.attrib.get("top", 0))) < 5

    @staticmethod
    def get_meal_name(elements: list):
        return " ".join([el.text for el in elements])

    def soups(self):
        line = []
        meal = ""
        price = ""

        for idx, elem in enumerate(self.text_elements):
            if "polévka" in elem.text:
                continue
            if "menu" in elem.text:
                element = [el for el in self.text_elements if el.text == "jídel"][0]
                self.update_elements(self.text_elements.index(element))
                if line:
                    if price:
                        self.results[self.get_meal_name(line)] = price
                    else:
                        meal = list(self.results)[-1]
                        price = self.results[meal]
                        del self.results[meal]
                        meal = meal + " " + self.get_meal_name(line)
                        self.results[meal] = price
                break
            if meal and price:
                self.results[meal] = price
                price = ""
                meal = ""
                line = []
            if not line:
                line.append(elem)
            else:
                if self.is_on_one_line(elem, line[-1]):
                    if ",-" not in elem.text:
                        line.append(elem)
                        continue
                    else:
                        price = elem.text
                        meal = self.get_meal_name(line)

    def main_courses(self):
        line = []
        meal = ""
        price = ""

        for idx, elem in enumerate(self.text_elements):
            if "*" in elem.text:
                break
            if meal and price:
                self.results[meal] = price
                price = ""
                meal = ""
                line = []
            if not line:
                line.append(elem)
            else:
                if self.is_on_one_line(elem, line[-1]):
                    if ",-" not in elem.text:
                        line.append(elem)
                        continue
                    else:
                        price = elem.text
                        meal = self.get_meal_name(line)
                else:
                    if ",-" not in [el.text for el in line]:
                        meal = list(self.results)[-1]
                        price = self.results[meal]
                        del self.results[meal]
                        meal = meal + ", " + self.get_meal_name(line)
                        self.results[meal] = price


if __name__ == "__main__":
    a = ParseZelenaLiska("menu_zelenaliska.xml")
    print(a.run())
