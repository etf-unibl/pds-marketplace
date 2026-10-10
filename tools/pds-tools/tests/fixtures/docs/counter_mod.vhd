-----------------------------------------------------------------------------
--
-- unit name:     counter_mod
--
-- description:
--
--   This file implements a modulo counter.
--
-----------------------------------------------------------------------------
-- The MIT License
-----------------------------------------------------------------------------
-- Copyright (c) 2026 Faculty of Electrical Engineering
--
-- Permission is hereby granted, free of charge, to any person obtaining a
-- copy of this software and associated documentation files (the "Software"),
-- to deal in the Software without restriction, including without limitation
-- the rights to use, copy, modify, merge, publish, distribute, sublicense,
-- and/or sell copies of the Software, and to permit persons to whom
-- the Software is furnished to do so, subject to the following conditions:
--
-- The above copyright notice and this permission notice shall be included in
-- all copies or substantial portions of the Software.
--
-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
-- IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
-- FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
-- THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
-- LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
-- ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
-- OTHER DEALINGS IN THE SOFTWARE
-----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity counter_mod is
  generic (
    g_WIDTH : natural := 4;
    g_MOD   : natural := 10
  );
  port (
    clk_i   : in    std_logic;
    rst_i   : in    std_logic;
    en_i    : in    std_logic; -- count enable
    count_o : out   std_logic_vector(g_WIDTH - 1 downto 0);
    tc_o    : out   std_logic
  );
end entity counter_mod;

architecture arch of counter_mod is

  constant c_LAST : natural := g_MOD - 1;

  type t_state is (idle, counting);

  signal count_reg  : unsigned(g_WIDTH - 1 downto 0);
  signal count_next : unsigned(g_WIDTH - 1 downto 0);
  signal state      : t_state;

  function is_last (value : unsigned) return boolean is
  begin
    return to_integer(value) = c_LAST;
  end function is_last;

begin

  count_reg_proc : process(clk_i) is
  begin
    if rising_edge(clk_i) then
      if rst_i = '1' then
        count_reg <= (others => '0');
      else
        count_reg <= count_next;
      end if;
    end if;
  end process count_reg_proc;

  process(all) is
  begin
    if en_i = '1' then
      if is_last(count_reg) then
        count_next <= (others => '0');
      else
        count_next <= count_reg + 1;
      end if;
    else
      count_next <= count_reg;
    end if;
  end process;

  sync_inst : entity work.decoder_2_4
    port map (
      a_i  => std_logic_vector(count_reg(1 downto 0)),
      en_i => en_i,
      y_o  => open
    );

  state   <= counting when en_i = '1' else idle;
  count_o <= std_logic_vector(count_reg);
  tc_o    <= '1' when is_last(count_reg) and en_i = '1' else '0';

end architecture arch;
