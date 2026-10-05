library ieee;
use ieee.std_logic_1164.all;

entity inv_tb is
end inv_tb;

architecture tb of inv_tb is
  component inv
    port (a : in std_logic; y : out std_logic);
  end component;
  signal a, y : std_logic;
begin
  uut : inv port map (a => a, y => y);
  process
  begin
    a <= '0';
    wait for 10 ns;
    assert y = '1' report "inverter output wrong for 0" severity error;
    a <= '1';
    wait for 10 ns;
    assert y = '0' report "inverter output wrong for 1" severity error;
    wait;
  end process;
end tb;
