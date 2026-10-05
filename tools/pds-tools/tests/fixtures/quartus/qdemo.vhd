library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity qdemo is
  port (
    clk, reset : in std_logic;
    a, b       : in std_logic_vector(7 downto 0);
    sel        : in std_logic;
    eq, y      : out std_logic;
    cnt        : out std_logic_vector(7 downto 0)
  );
end qdemo;

architecture rtl of qdemo is
  signal r : unsigned(7 downto 0);
begin
  -- latch: no else branch
  process(a, b)
  begin
    if a = b then
      eq <= '1';
    end if;
  end process;
  -- incomplete sensitivity list
  process(sel)
  begin
    y <= sel and a(0);
  end process;
  process(clk, reset)
  begin
    if reset = '1' then
      r <= (others => '0');
    elsif rising_edge(clk) then
      r <= r + unsigned(b);
    end if;
  end process;
  cnt <= std_logic_vector(r);
end rtl;
