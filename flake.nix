{
  description = "HRI CW 2";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/23.05";
  };

  outputs = { self, nixpkgs }: 
  let 
    system = "aarch64-darwin";
    pkgs = nixpkgs.legacyPackages.${system};
  in
  {
    devShells.${system}.default = pkgs.mkShell rec {
    name = "CookRobotENV";

    packages = with pkgs; [ 
      python311Packages.pygame
    ];

    shellHook = ''
      export PS1="\e[0;31m[\u@\h \W]\$ \e[m " 
    '';
  };
    
  };
}
