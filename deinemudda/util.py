#  Copyright (c) 2019 Markus Ressel
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Message


def build_menu(table: [[(str, str)]]) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard from a (text, data) tuple matrix
    :param table: list of lists containing (text, data) tuples
    :return: inline keyboard markup
    """
    from emoji import emojize

    menu = []
    for row in table:
        column_items = []
        for column in row:
            text = emojize(column[0], use_aliases=True)
            callback_data = column[0] if column[1] is None or len(column[1]) <= 0 else column[1]
            column_items.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        menu.append(column_items)

    return InlineKeyboardMarkup(menu, n_cols=len(menu[0]))


def send_message(bot: Bot, chat_id: str, message: str, parse_mode: str = None, reply_to: int = None,
                 menu: InlineKeyboardMarkup = None) -> Message:
    """
    Sends a text message to the given chat
    :param bot: the bot
    :param chat_id: the chat id to send the message to
    :param message: the message to chat (may contain emoji aliases)
    :param parse_mode: specify whether to parse the text as markdown or HTML
    :param reply_to: the message id to reply to
    :param menu: inline keyboard menu markup
    """
    from emoji import emojize

    emojized_text = emojize(message, use_aliases=True)
    return bot.send_message(chat_id=chat_id, parse_mode=parse_mode, text=emojized_text, reply_to_message_id=reply_to,
                            reply_markup=menu)


def import_submodules(package, recursive=True) -> dict:
    """ Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :param recursive: loads all subpackages
    :type package: str | module
    :rtype: dict[str, types.ModuleType]
    """
    import pkgutil
    import importlib

    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results.update(import_submodules(full_name))
    return results


def get_all_subclasses(base_class):
    """
    Returns a list of all currently imported classes that are subclasses (even multiple levels)
    of the specified base class.
    :param base_class: base class to match classes to
    :return: list of classes
    """
    all_subclasses = []

    for subclass in base_class.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def find_implementations(base_type: type, base_package) -> [any]:
    """
    Finds implementations of the given base_type in the given package by recursively searching through
    subpackages and finding classes that have the base_type as a superclass.
    """
    import_submodules(base_package)
    result = []
    for implementation in get_all_subclasses(base_type):
        # ignore classes that are disabled by the developer
        if hasattr(implementation, "DISABLED") and implementation.DISABLED is True:
            continue

        result.append(implementation)

    return result
