"""Command Completion for pymodbus REPL."""
from prompt_toolkit.application.current import get_app

# pylint: disable=missing-type-doc
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.filters import Condition
from prompt_toolkit.styles import Style

from pymodbus.repl.client.helper import get_commands


@Condition
def has_selected_completion():
    """Check for selected completion."""
    complete_state = get_app().current_buffer.complete_state
    return complete_state is not None and complete_state.current_completion is not None


style = Style.from_dict(
    {
        "completion-menu.completion": "bg:#008888 #ffffff",
        "completion-menu.completion.current": "bg:#00aaaa #000000",
        "scrollbar.background": "bg:#88aaaa",
        "scrollbar.button": "bg:#222222",
    }
)


class CmdCompleter(Completer):
    """Completer for Pymodbus REPL."""

    def __init__(self, client=None, commands=None, ignore_case=True):
        """Initialize.

        :param client: Modbus Client
        :param commands: Commands to be added for Completion (list)
        :param ignore_case: Ignore Case while looking up for commands
        """
        self._commands = commands or get_commands(client)
        self._commands["help"] = ""
        self._command_names = self._commands.keys()
        self.ignore_case = ignore_case

    @property
    def commands(self):
        """Return commands."""
        return self._commands

    @property
    def command_names(self):
        """Return command names."""
        return self._commands.keys()

    def completing_command(self, words, word_before_cursor):
        """Determine if we are dealing with supported command.

        :param words: Input text broken in to word tokens.
        :param word_before_cursor: The current word before the cursor, \
            which might be one or more blank spaces.
        :return:
        """
        return len(words) == 1 and len(word_before_cursor)

    def completing_arg(self, words, word_before_cursor):
        """Determine if we are currently completing an argument.

        :param words: The input text broken into word tokens.
        :param word_before_cursor: The current word before the cursor, \
            which might be one or more blank spaces.
        :return: Specifies whether we are currently completing an arg.
        """
        return len(words) > 1 and len(word_before_cursor)

    def arg_completions(
        self, words, word_before_cursor
    ):  # pylint: disable=unused-argument
        """Generate arguments completions based on the input.

        :param words: The input text broken into word tokens.
        :param word_before_cursor: The current word  before the cursor, \
            which might be one or more blank spaces.
        :return: A list of completions.
        """
        cmd = words[0].strip()
        cmd = self._commands.get(cmd, None)
        return cmd if cmd else None

    def _get_completions(self, word, word_before_cursor):
        """Get completions."""
        if self.ignore_case:
            word_before_cursor = word_before_cursor.lower()
        return self.word_matches(word, word_before_cursor)

    def word_matches(self, word, word_before_cursor):
        """Match the word and word before cursor.

        :param word: The input text broken into word tokens.
        :param word_before_cursor: The current word before the cursor, \
            which might be one or more blank spaces.
        :return: True if matched.

        """
        if self.ignore_case:
            word = word.lower()
        return word.startswith(word_before_cursor)

    def get_completions(self, document, complete_event):
        """Get completions for the current scope.

        :param document: An instance of `prompt_toolkit.Document`.
        :param complete_event: (Unused).
        :return: Yields an instance of `prompt_toolkit.completion.Completion`.
        """
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        text = document.text_before_cursor.lstrip()
        words = document.text.strip().split()
        meta = None
        commands = []
        if not words:
            # yield commands
            pass
        if self.completing_command(words, word_before_cursor):
            commands = self._command_names
            c_meta = {
                k: v.help_text if not isinstance(v, str) else v
                for k, v in self._commands.items()
            }
            meta = lambda x: (  # pylint: disable=unnecessary-lambda-assignment
                x,
                c_meta.get(x, ""),
            )
        else:
            if not list(
                filter(lambda cmd: any(x == cmd for x in words), self._command_names)
            ):
                # yield commands
                pass

            if " " in text:
                command = self.arg_completions(words, word_before_cursor)
                commands = list(command.get_completion())
                commands = list(
                    filter(lambda cmd: not (any(cmd in x for x in words)), commands)
                )
                meta = command.get_meta
        for command in commands:
            if self._get_completions(command, word_before_cursor):
                _, display_meta = meta(command) if meta else ("", "")
                yield Completion(
                    command, -len(word_before_cursor), display_meta=display_meta
                )
