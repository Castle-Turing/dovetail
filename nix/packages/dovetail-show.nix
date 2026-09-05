# `dovetail-show`, the show verb, as a package.
#
# Everything it needs beyond its own targeting rule — the compositor
# seam, the editor seam, the process table, and the launch machinery,
# along with the store paths baked into them — comes from
# `dovetail-seams`.
{
  lib,
  python3Packages,
  dovetail-seams,
}:

python3Packages.buildPythonApplication {
  pname = "dovetail-show";
  version = "0.1.0";
  pyproject = true;

  src = ../../tools/dovetail-show;

  build-system = [ python3Packages.setuptools ];

  dependencies = [ dovetail-seams ];

  # The unit tests over the targeting rule run as part of building the
  # package, so `nix flake check` gets them by depending on this output.
  nativeCheckInputs = [ python3Packages.pytestCheckHook ];

  pythonImportsCheck = [ "dovetail_show" ];

  meta = {
    description = "Open a file in the focused Dovetail editor, or in a new floating one";
    mainProgram = "dovetail-show";
    license = lib.licenses.mit;
    platforms = lib.platforms.unix;
  };
}
