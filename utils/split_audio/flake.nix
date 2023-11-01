{
  description = "Development";

  inputs = {
    nixpkgs.url      = "github:NixOS/nixpkgs/nixos-unstable";
    rust-overlay.url = "github:oxalica/rust-overlay";
    flake-utils.url  = "github:numtide/flake-utils";
  };

  outputs = { nixpkgs, rust-overlay, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs {
          inherit system overlays;
        };
        libDeps = with pkgs; [
          alsa-lib
        ];
        libPath = pkgs.lib.makeLibraryPath libDeps;
      in
      with pkgs;
      {
        devShells.default = mkShell {
          packages = [
            python3
            ffmpeg
          ];
          buildInputs = libDeps ++ [
            rust-bin.stable.latest.default
          ];
          shellHook = ''
            export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:${libPath}"
          '';
        };
      }
    );
}
