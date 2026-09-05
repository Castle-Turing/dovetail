# `dovetail-seams`, the machinery Dovetail's verbs share, as a Python
# library package. It installs no executables; `dovetail-show` and
# `dovetail-scriptorium` both depend on it.
#
# Three absolute store paths are baked in here, and they are the only
# build-time configuration any Dovetail verb has:
#
#   the editor to launch when nothing overrides it — this flake's own
#   `dovetail` package, overridable at runtime with $DOVETAIL_EDITOR;
#
#   the client used to talk to a running instance — plain unwrapped
#   Neovim, so a verb never depends on the configuration whose files it
#   is opening;
#
#   the REPL the scriptorium puts beside the editor — plain `python3`,
#   overridable at runtime with $DOVETAIL_REPL.
#
# `swaymsg` is deliberately *not* baked in and not added to the closure.
# It belongs to the resident's running compositor, is found on $PATH,
# and its absence is an ordinary answer — "no focused editor", "no
# compositor to place windows with" — rather than an error.
#
# The terminal emulator is absent for a different reason: Dovetail will
# not guess one, and refuses instead. See `docs/show.md`.
{
  lib,
  python3,
  python3Packages,
  neovim-unwrapped,
  dovetail-nvim,
}:

python3Packages.buildPythonPackage {
  pname = "dovetail-seams";
  version = "0.1.0";
  pyproject = true;

  src = ../../tools/dovetail-seams;

  build-system = [ python3Packages.setuptools ];

  postPatch = ''
    substituteInPlace src/dovetail_seams/defaults.py \
      --replace-fail '@dovetailEditor@' '${lib.getExe' dovetail-nvim "nvim"}' \
      --replace-fail '@dovetailNvimClient@' '${lib.getExe' neovim-unwrapped "nvim"}' \
      --replace-fail '@dovetailRepl@' '${lib.getExe python3}'
  '';

  # The unit tests over the seams run as part of building the package, so
  # `nix flake check` gets them by depending on this output.
  nativeCheckInputs = [ python3Packages.pytestCheckHook ];

  pythonImportsCheck = [ "dovetail_seams" ];

  meta = {
    description = "The compositor, editor, process and launch seams Dovetail's verbs share";
    license = lib.licenses.mit;
    platforms = lib.platforms.unix;
  };
}
