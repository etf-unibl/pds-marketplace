--! @file
--! @brief Documentation pitfalls checked with Doxygen 1.9.5

library ieee;
use ieee.std_logic_1164.all;

--! Multi line entity comment
--! without a brief command
entity pitfalls is
  port (
    clk_i : in    std_logic; --! Clock
    rst_i : in    std_logic; --! Reset, joined with the comment below
    --! Data input
    d_i   : in    std_logic;
    q_o   : out   std_logic  -- plain comment, not in the documentation
  );
end entity pitfalls;

--! @brief Architecture brief

--! @details Details separated by a blank line
architecture arch of pitfalls is

  --! Two signals share this comment
  signal s1, s2 : std_logic;
  signal s3     : std_logic; --! TODO: describe s3
  --! @brief First sentence of a long brief. Second sentence of the brief.
  signal s4     : std_logic;

begin

  process(clk_i) is
  begin
    if rising_edge(clk_i) then
      s1 <= d_i;
    end if;
  end process;

  --! Register of the output
  q_reg : process(clk_i) is
  begin
    if rising_edge(clk_i) then
      q_o <= s1;
    end if;
  end process q_reg;

  s2 <= rst_i;
  s3 <= s2;
  s4 <= s3;
  --! Comment before the end of the architecture
end architecture arch;
