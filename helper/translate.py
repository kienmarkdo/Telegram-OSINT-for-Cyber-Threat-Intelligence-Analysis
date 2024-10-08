"""
This module provides offline translation for the text that is collected from Telegram.

The argos-translate translation module is used for this project
https://github.com/argosopentech/argos-translate

It is important that the translation be offline as this application may be used to collect
sensitive data from various groups. As such, it is in the user's best interest to keep the
data private from translation services' servers.
"""

import logging

import argostranslate.apis
import argostranslate.argospm
import argostranslate.package
import argostranslate.translate
from lingua import Language, LanguageDetectorBuilder


def translate(text: str) -> str | None:
    """
    Auto-detects the language of a given piece of text and translates it to English.
    If the text is already in English, no translation will be done.

    Args:
        text: the text to be translated into English e.g. "Hola mi amigo. ¿Cómo estás hoy?"

    Returns:
        The text translated into English e.g. "Hello my friend. How are you today?".
        None is the text is already in English.
    """
    if text is None or text == "":
        return None

    # Attempt to detect the ISO 639 code of the source language (e.g. "en" for English)
    # NOTE: Feel free to add/remove languages from this list as needed
    languages_to_detect = [
        Language.ENGLISH,
        Language.SPANISH,
        Language.RUSSIAN,
        Language.GERMAN,
        Language.ITALIAN,
        Language.FRENCH,
        Language.CHINESE,
        Language.UKRAINIAN,
        Language.SLOVAK,
        Language.DUTCH,
        Language.TURKISH,
        Language.DANISH,
    ]
    # Store ISO 639 code of supported languages
    # NOTE: Feel free to add/remove languages from this list as needed
    languages_to_detect_code = [x.iso_code_639_1.name.lower() for x in languages_to_detect]
    # NOTE: All languages (WARNING. USES A LOT OF RAM AND CPU)
    # languages_to_detect_code = [x.iso_code_639_1.name.lower() for x in Language.all()]  # ['en', 'fr',...] all 75 langs

    # Detect language
    detector = LanguageDetectorBuilder.from_languages(*languages_to_detect).build()  # Detect listed languages
    # detector = LanguageDetectorBuilder.from_all_languages().with_preloaded_language_models().build()  # Detect all languages available in the library (eager loading)
    # detector = LanguageDetectorBuilder.from_all_languages().build()  # Detect all languages available in the library (lazy loading)
    language_detected = detector.detect_language_of(text)

    if language_detected is None:
        logging.debug(f"Unable to detect the language of this text")
        return (
            "Requires manual translation. Unable to detect the language of this text."
        )

    # No translation is returned if the text is in English
    from_code = language_detected.iso_code_639_1.name.lower()
    if from_code == "en":
        return None
    elif from_code is None or from_code == "":
        logging.error(
            f"Unexpectedly unable to detect nor translate the following text: {text}"
        )
        return None

    # Verify that the source language's translation package is installed
    to_code = "en"
    logging.debug(
        f"Translating the following text from '{from_code}' to '{to_code}': {text}"
    )
    if from_code not in languages_to_detect_code:
        logging.info(
            f"Unable to translate '{from_code}' -> {to_code}. "
            f"The translation package for '{from_code}' has not been installed."
        )
        logging.info(f"Skipping translation...")
        return (
            f"Requires manual translation. "
            f"Translation for the following language is not yet supported '{from_code}'."
        )
        # logging.info(
        #     f"New language detected. Installing language translation package: '{from_code}'"
        # )
        # # Download the language if it is supported
        # if from_code in get_installed_languages()
        #     install_language(from_code)

    # Translate text
    logging.debug(f"Translating: ", text)
    translatedText = argostranslate.translate.translate(text, from_code, to_code)

    return translatedText


def get_installed_languages() -> list[argostranslate.translate.Language]:
    """
    Lists languages that have been installed locally and can be translated offline.

    Returns:
        List of languages that can be translated locally.
    """
    languages = argostranslate.translate.get_installed_languages()
    # Print the list of installed languages
    # print(f"Number of languages installed: {len(languages)}")
    # for lang in languages:
    #     print(f"- {lang}")
    return languages


def install_language(from_code: str):
    """
    Downloads and installs the offline translation package of a given language to English.

    e.g. Download the Spanish -> English ("es" -> "en") translation package

    Args:
        from_code: the ISO 639 code of the source language (e.g. "en" for English)
    """
    if from_code is None or from_code == "":
        logging.error(
            f"A language code was not provided. Please provide a language code."
        )
        return
    to_code = "en"

    # Download and install Argos Translate package
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package_to_install = next(
        filter(
            lambda x: x.from_code == from_code and x.to_code == to_code,
            available_packages,
        )
    )
    argostranslate.package.install_from_path(package_to_install.download())


def install_all_languages():
    """
    Downloads and installs all offline translation packages.
    Translation packages are <source_language> to English.

    A complete list of source languages can be found in the link below
    https://github.com/argosopentech/argos-translate?tab=readme-ov-file#supported-languages

    Args:
        from_code: the ISO 639 code of the source language (e.g. "en" for English)
    """
    argostranslate.argospm.install_all_packages()


if __name__ == "__main__":
    # Execute "python translate.py" to view the demo below
    print(translate("languages are awesome"))
    print(translate("Hola mi amigo. ¿Cómo estás hoy?"))
    print(translate("Здравствуй, друг. Как вы сегодня?"))
