import eel


def main():
    eel.init("app")
    eel.start("pages/index.html", size=(900, 600), jinja_templates="pages")


if __name__ == "__main__":
    main()
