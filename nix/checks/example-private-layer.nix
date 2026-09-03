# A stand-in for a resident's private layer, used by the `overlay-point`
# check. It carries nothing but taste — a colorscheme and a keymap — and
# exists to keep `docs/module.md`'s worked example an honest claim rather
# than a hopeful one.
#
# A real private layer lives outside this repository (see the note in
# `docs/module.md` about flake-tracked trees and the Nix store). This one
# uses only what ships with Neovim, so the check costs nothing to build.
{
  colorscheme = "habamax";

  keymaps = [
    {
      mode = "n";
      key = "<leader>w";
      action = "<cmd>write<cr>";
      options.desc = "Write the current buffer";
    }
    {
      # Moving by display line is exactly the kind of prose preference
      # the module leaves alone: it belongs here, not in the mechanism.
      mode = [
        "n"
        "x"
      ];
      key = "j";
      action = "gj";
      options.desc = "Down by display line";
    }
  ];
}
