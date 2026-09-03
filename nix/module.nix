# The Dovetail nixvim module.
#
# Public mechanism only: reachability over a socket, treesitter, and a
# minimal set of prose-friendly markdown defaults. Everything that is
# taste — colorschemes, keymaps, typefaces, statuslines — belongs to the
# private layer, which composes with this module by being imported
# alongside it. See `docs/module.md`.
{ config, ... }:
{
  # --------------------------------------------------------------------
  # Every instance is born reachable.
  #
  # One socket per instance at $XDG_RUNTIME_DIR/dovetail/nvim-<pid>.sock,
  # started from the shipped configuration so the guarantee travels with
  # the configuration rather than with one launch path. An agent never
  # configures this at runtime; it only connects.
  #
  # This runs in `extraConfigLuaPre` so the socket exists before any
  # private-layer configuration gets a chance to fail: a broken overlay
  # should still leave an instance you can reach and inspect.
  #
  # Two globals report the outcome, and nothing is written to stderr:
  #   vim.g.dovetail_socket        the socket path, or nil
  #   vim.g.dovetail_socket_error  why there is no socket, or nil
  # --------------------------------------------------------------------
  extraConfigLuaPre = ''
    do
      local uv = vim.uv or vim.loop

      vim.g.dovetail_socket = nil
      vim.g.dovetail_socket_error = nil

      local runtime_dir = vim.env.XDG_RUNTIME_DIR

      if runtime_dir == nil or runtime_dir == "" then
        -- $XDG_RUNTIME_DIR is the whole basis of the scheme: per-user,
        -- tmpfs-backed and permission-safe by platform contract. With no
        -- such directory there is no safe path to fall back to, so this
        -- instance is simply not reachable, and says so.
        vim.g.dovetail_socket_error =
          "XDG_RUNTIME_DIR is unset; no Dovetail socket was started"
      else
        local dir = runtime_dir .. "/dovetail"
        -- 448 == 0700. $XDG_RUNTIME_DIR is already private by contract;
        -- this is belt and braces on a directory full of control channels.
        vim.fn.mkdir(dir, "p", 448)

        local path = string.format("%s/nvim-%d.sock", dir, uv.os_getpid())
        local started, err = pcall(vim.fn.serverstart, path)

        if started then
          vim.g.dovetail_socket = path

          vim.api.nvim_create_autocmd("VimLeavePre", {
            group = vim.api.nvim_create_augroup("dovetail_socket", { clear = true }),
            desc = "Remove this instance's Dovetail socket on clean exit",
            callback = function()
              pcall(vim.fn.serverstop, path)
              -- Consumers must tolerate stale sockets from unclean exits
              -- regardless; this only keeps the common case tidy.
              if uv.fs_stat(path) then
                pcall(uv.fs_unlink, path)
              end
            end,
          })
        else
          vim.g.dovetail_socket_error =
            "could not listen on " .. path .. ": " .. tostring(err)
        end
      end
    end
  '';

  # --------------------------------------------------------------------
  # Treesitter, including markdown.
  #
  # The grammar set is deliberately bounded rather than "every grammar
  # nixpkgs builds": markdown is the reason Dovetail exists, and the rest
  # are the languages this ecosystem's own trees are written in. The
  # option is a list, so a private layer adds grammars by listing more of
  # them in its own module — the lists concatenate.
  # --------------------------------------------------------------------
  plugins.treesitter = {
    enable = true;
    highlight.enable = true;
    indent.enable = true;

    grammarPackages = with config.plugins.treesitter.package.builtGrammars; [
      bash
      diff
      git_rebase
      gitcommit
      json
      lua
      markdown
      markdown_inline
      nix
      python
      query
      regex
      toml
      vim
      vimdoc
      yaml
    ];
  };

  # --------------------------------------------------------------------
  # Prose-friendly markdown defaults, buffer-local.
  #
  # Kept to the four settings that make soft-wrapped prose *legible*
  # rather than merely wrapped. Anything a resident might reasonably want
  # different — spell checking and its dictionary, `conceallevel`,
  # `showbreak`, remapping j/k to move by display line — is taste and
  # belongs in the overlay point, not here.
  # --------------------------------------------------------------------
  autoGroups.dovetail_prose.clear = true;

  autoCmd = [
    {
      group = "dovetail_prose";
      event = [ "FileType" ];
      pattern = [ "markdown" ];
      desc = "Dovetail prose defaults for markdown buffers";
      callback.__raw = ''
        function()
          -- Wrap at the window edge rather than running off it, ...
          vim.opt_local.wrap = true
          -- ... at word boundaries rather than mid-word, ...
          vim.opt_local.linebreak = true
          -- ... keeping continuation lines under the text they continue,
          -- which is what makes wrapped list items readable, ...
          vim.opt_local.breakindent = true
          -- ... and never rewriting the file to hard-wrap it, because a
          -- soft-wrapped buffer that silently inserts newlines produces
          -- diffs nobody asked for.
          vim.opt_local.textwidth = 0
        end
      '';
    }
  ];

  # Deliberately absent: `colorscheme`, `keymaps`, `opts`, statusline,
  # and every other cosmetic. They are left undefined so a private-layer
  # module can set them without fighting a default it did not ask for.
}
