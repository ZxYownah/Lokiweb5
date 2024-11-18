#import pyfiglet
from pyfiglet import Figlet


def generate_banner(text, font='slant'):
    """Generates a banner for the given text using pyfiglet.

    Args:
      text: The text to display in the banner.
      font: The pyfiglet font to use. See pyfiglet docs for options.

    Returns:
      A string containing the banner.
    """

    fig = Figlet(font=font)
    banner = fig.renderText(text)
    return banner


if __name__ == "__main__":
    text = input("Enter the text for your banner: ")
    banner = generate_banner(text)
    print(banner)