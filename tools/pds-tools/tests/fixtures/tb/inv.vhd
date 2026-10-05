library ieee;
use ieee.std_logic_1164.all;

entity inv is
  port (a : in std_logic; y : out std_logic);
end inv;

architecture rtl of inv is
begin
  y <= not a;
end rtl;
