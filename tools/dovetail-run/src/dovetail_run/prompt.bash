# The prompt the resident is handed. Run by `dovetail-run` as the
# trailing arguments of the terminal the resident named, with exactly
# two arguments: the provenance block to print, and the command to
# pre-fill. Both have already been refused-or-passed by `sanitize.py`,
# so nothing here has to defend against a newline or an escape sequence.
#
# It is not executable and has no shebang: the verb names bash by store
# path and hands this file to it, so the shell that runs the prompt is
# the one the package was built with rather than whatever `env` finds.
#
# The one rule this file exists to keep is that the line the resident
# reads is the line that runs. So it does nothing to that line: no
# expansion before it is displayed, no rewriting after it is accepted,
# and no default answer. `read -e` is a real readline line — arrow keys,
# word motions, kill and yank all work — and `-i` seeds it with the
# proposal rather than typing it for her.

if [ "$#" -ne 2 ]; then
    printf 'dovetail-run: the prompt wrapper takes two arguments, got %d\n' "$#" >&2
    exit 2
fi

provenance=$1
proposal=$2

# Nothing is written to any history file. The resident's shell history
# belongs to the resident's shell, and a one-shot prompt appending to it
# uninvited would put a command she may never have run into the record
# she greps. `read -e` does not add to the history list on its own; this
# makes sure nothing else can either.
unset HISTFILE
set +o history

# No terminal means the line cannot be displayed, and a line that cannot
# be displayed must not run: the whole promise is that she read it. This
# is the case where a terminal argv prefix runs its argument without a
# tty — refuse rather than quietly reading the proposal from a pipe.
if [ ! -t 0 ]; then
    printf 'dovetail-run: no terminal on standard input, so the command cannot be shown; nothing was run\n' >&2
    exit 2
fi

printf '%s\n\n' "$provenance"

# `-r` so a backslash in the proposal survives as a backslash. IFS
# emptied so leading and trailing spaces are not eaten: what is
# displayed is what runs, byte for byte, and trimming would be a repair.
if ! IFS= read -e -r -i "$proposal" -p '$ ' line; then
    printf '\ndovetail-run: end of input; nothing was run.\n'
    exit 0
fi

if [ -z "${line//[[:space:]]/}" ]; then
    printf 'dovetail-run: the line was cleared; nothing was run.\n'
    exit 0
fi

eval "$line"
status=$?

# The window belongs to the resident until she is finished reading it.
# A terminal that closes on the command's last line of output is a
# command whose output nobody saw.
printf '\ndovetail-run: exit status %d. Press Enter to close this window.' "$status"
read -r _ || true
exit "$status"
