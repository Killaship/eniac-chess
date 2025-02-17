import unittest
import textwrap
from easm import SymbolTable, Assembler, format_comment, OutOfResources, SyntaxError, Macro

class TestSymbolTable(unittest.TestCase):

  def test_lookup(self):
    # if we allocate the same name twice, we should get the same number
    # but a new name needs a different number
    for typ in ['a','p','d','ad.s','ad.d','ad.dp','ad.sd']:
      s = SymbolTable()

      n1 = s.lookup(typ,'nameA')
      self.assertEqual(n1, 0)
      n2 = s.lookup(typ,'nameA')
      self.assertEqual(n1, n2)
      n3 = s.lookup(typ,'nameB')
      self.assertNotEqual(n1, n3)

  def test_lookup_acc(self):
    # like test_lookup but with the resources on an accumulator
    acc_idx = 5

    for typ in ['r','t','i']:
      s = SymbolTable()

      n1 = s.lookup_acc(acc_idx, typ,'nameA')
      self.assertEqual(n1, (0, typ))
      n2 = s.lookup_acc(acc_idx, typ,'nameA')
      self.assertEqual(n1, n2)
      n3 = s.lookup_acc(acc_idx, typ,'nameB')
      self.assertNotEqual(n1, n3)

  def test_lookup_acc_x_uses_r(self):
    acc_idx = 5
    s = SymbolTable()
    n1 = s.lookup_acc(acc_idx, 'x', 'nameA')
    self.assertEqual(n1, (0, 'r'))

  def test_lookup_acc_x_uses_t_if_no_r(self):
    acc_idx = 5
    s = SymbolTable()
    # consume all the r-s
    for n in range(4):
      _ = s.lookup_acc(acc_idx, 'r', str(n))
    # x should now use t- instead
    n1 = s.lookup_acc(acc_idx, 'x', 'nameA')
    self.assertEqual(n1, (0, 't'))

  def test_acc_distinct(self):
    s = SymbolTable()
    n1 = s.lookup_acc(9,'r','receiver')
    n2 = s.lookup_acc(19,'r','receiver')
    self.assertEqual(n1, n2) # should have same number, b/c different accs

  def test_out_of_resources(self):
      s = SymbolTable()
      for i in range(20):
        s.lookup('a','name' + str(i))
      with self.assertRaises(OutOfResources):
        s.lookup('a','onemore')


  def test_define(self):
      s = SymbolTable()
      s.define('p','myprogram',55)

      n = s.lookup('p','otherprogram')
      self.assertNotEqual(n, 55)        # shouldn't be the number we defined

      n = s.lookup('p','myprogram')
      self.assertEqual(n, 55)           # should still be at same value


class TestAssembler(unittest.TestCase):

  def test_literal(self):
      a = Assembler()
      self.assertEqual(a.assemble_line('p 1-1 a3.5i'),'p 1-1 a3.5i') 
      self.assertEqual(a.assemble_line('p 8 ad.dp.1.11'), 'p 8 ad.dp.1.11')

  def test_indents_and_comments(self):
      a = Assembler()
      self.assertEqual(a.assemble_line(''), '')

      # test comment alignment and preservation of leading ws
      self.assertEqual(a.assemble_line('s a2.cc7 C   # then clear'),'s a2.cc7 C                    # then clear') 
      self.assertEqual(a.assemble_line(' p a2.5o a3.4i # next program'),' p a2.5o a3.4i                # next program') 
      self.assertEqual(a.assemble_line(' s a2.cc7 C   # then clear'),' s a2.cc7 C                   # then clear')

  def test_define(self):
      a = Assembler()

      # Test that we can set symbols to constants
      self.assertEqual(
        a.assemble_line('{p-name}=5-5'), '# {p-name}=5-5')
      self.assertEqual(
        a.assemble_line('p {p-name} a3.5i'), format_comment('p 5-5 a3.5i','# 5-5=p-name'))
      self.assertEqual(
        a.assemble_line('{d-name}=5'), '# {d-name}=5')
      self.assertEqual(
        a.assemble_line('p {d-name} a3.g'), format_comment('p 5 a3.g','# 5=d-name'))
      self.assertEqual(
        a.assemble_line('{a-name}=a13'), '# {a-name}=a13')
      self.assertEqual(
        a.assemble_line('p 1 {a-name}.d'), format_comment('p 1 a13.d','# a13=a-name'))

      # Test that we can alias previously allocated resources
      self.assertEqual(
        a.assemble_line('{p-name2}={p-name}'), '# {p-name2}={p-name}')
      self.assertEqual(
        a.assemble_line('p {p-name2} a3.5i'), format_comment('p 5-5 a3.5i','# 5-5=p-name2'))
      self.assertEqual(
        a.assemble_line('{d-name2}={d-name}'), '# {d-name2}={d-name}')
      self.assertEqual(
        a.assemble_line('p {d-name2} a3.g'), format_comment('p 5 a3.g','# 5=d-name2'))
      self.assertEqual(
        a.assemble_line('{a-name2}={a-name}'), '# {a-name2}={a-name}')
      self.assertEqual(
        a.assemble_line('p 1 {a-name2}.d'), format_comment('p 1 a13.d','# a13=a-name2'))


  # test several things for each type of resource:
  #  - intitial allocation of the first resource on the machine (e.g. 1-1)
  #  - replacement of the same name with same resource
  #  - allocation of a different name to a different resource
  #  - running out of resources

  # test that there are exactly numleft resources, then we error
  def run_out(self, a, prefix, suffix, numleft):
    for i in range(numleft):
      a.assemble_line(prefix + str(i) + suffix)
    with self.assertRaises(OutOfResources):
      a.assemble_line(prefix + str(numleft) + suffix)

  def test_program_line(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p {p-name} a3.5i'), format_comment('p 1-1 a3.5i','# 1-1=p-name'))
    self.assertEqual(
      a.assemble_line('p {p-name} a4.1i'), format_comment('p 1-1 a4.1i','# 1-1=p-name'))
    self.assertEqual(
      a.assemble_line('p a13.5o {p-other-name}'), format_comment('p a13.5o 1-2','# 1-2=p-other-name'))
    self.assertEqual(
      a.assemble_line('p i.io {p-other-name}'), format_comment('p i.io 1-2','# 1-2=p-other-name'))
    self.run_out(a, 'p {p-', '} a1.1i', 26*11-2)

  def test_data_trunk(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p {d-name} a3.a'), format_comment('p 1 a3.a','# 1=d-name')) 
    self.assertEqual(
      a.assemble_line('p a4.S {d-name}'),format_comment('p a4.S 1','# 1=d-name')) 
    self.assertEqual(
      a.assemble_line('p a16.A {d-other-name} '),format_comment('p a16.A 2','# 2=d-other-name'))
    self.run_out(a, 'p {d-', '} a1.a', 18)

  def test_shift_adapter(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p a20.A ad.s.{ad-name}.3'), format_comment('p a20.A ad.s.1.3','# 1=ad-name'))
    self.assertEqual(
      a.assemble_line('p ad.s.{ad-other-name}.3 a11.g'), format_comment('p ad.s.2.3 a11.g','# 2=ad-other-name'))
    self.assertEqual(
      a.assemble_line('p 2 ad.s.{ad-other-name}.4'), format_comment('p 2 ad.s.2.4','# 2=ad-other-name'))
    self.run_out(a, 'p ad.s.{ad-', '}.1 a1.a', 78)

  def test_deleter_adapter(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p a20.A ad.d.{ad-name}.3'), format_comment('p a20.A ad.d.1.3','# 1=ad-name'))
    self.assertEqual(
      a.assemble_line('p ad.d.{ad-other-name}.3 a11.g'), format_comment('p ad.d.2.3 a11.g','# 2=ad-other-name'))
    self.assertEqual(
      a.assemble_line('p 3 ad.d.{ad-other-name}.3 '), format_comment('p 3 ad.d.2.3','# 2=ad-other-name'))
    self.run_out(a, 'p ad.d.{ad-', '}.1 a1.a', 78)

  def test_digit_pulse_adapter(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p a20.A ad.dp.{ad-name}.11'), format_comment('p a20.A ad.dp.1.11','# 1=ad-name'))
    self.assertEqual(
      a.assemble_line('p a20.A ad.dp.{ad-other-name}.11'), format_comment('p a20.A ad.dp.2.11','# 2=ad-other-name'))
    self.assertEqual(
      a.assemble_line('p ad.dp.{ad-other-name}.11 5-5'), format_comment('p ad.dp.2.11 5-5','# 2=ad-other-name'))
    self.run_out(a, 'p ad.dp.{ad-', '}.11 5-5', 78)

  def test_special_digit_adapter(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p a20.A ad.sd.{ad-name}.8'), format_comment('p a20.A ad.sd.1.8','# 1=ad-name'))
    self.assertEqual(
      a.assemble_line('p a20.A ad.sd.{ad-other-name}.8'), format_comment('p a20.A ad.sd.2.8','# 2=ad-other-name'))
    self.assertEqual(
      a.assemble_line('p ad.sd.{ad-other-name}.8 4'), format_comment('p ad.sd.2.8 4','# 2=ad-other-name'))
    self.run_out(a, 'p ad.sd.{ad-', '}.8 1', 78)

  def test_permute_adapter(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p a20.A ad.permute.10'), 'p a20.A ad.permute.10')
    self.assertEqual(
      a.assemble_line('s ad.permute.10 11.1.2.3.4.5.6.7.8.9.10'), 's ad.permute.10 11.1.2.3.4.5.6.7.8.9.10')
    
    self.assertEqual(
      a.assemble_line('p a20.A ad.permute.{ad-name}'), format_comment('p a20.A ad.permute.1','# 1=ad-name'))
    self.assertEqual(
      a.assemble_line('p a20.A ad.permute.{ad-other-name}'), format_comment('p a20.A ad.permute.2','# 2=ad-other-name'))
    self.assertEqual(
      a.assemble_line('p ad.permute.{ad-other-name} 4'), format_comment('p ad.permute.2 4','# 2=ad-other-name'))
    
    self.assertEqual(
      a.assemble_line('s ad.permute.{ad-name} 11.1.2.3.4.5.6.7.8.9.10'), format_comment('s ad.permute.1 11.1.2.3.4.5.6.7.8.9.10','# 1=ad-name'))

    self.run_out(a, 'p ad.permute.{ad-', '} 1', 78)


  def test_ftable(self):
    # we don't currently track resources on ftables but we should be able to patch to named lines
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p {p-name} f1.1i'), format_comment('p 1-1 f1.1i','# 1-1=p-name'))
    self.assertEqual(
      a.assemble_line('p f1.1o {p-other-name}'), format_comment('p f1.1o 1-2','# 1-2=p-other-name'))
    self.assertEqual(
      a.assemble_line('p {d-name} f1.arg'), format_comment('p 1 f1.arg','# 1=d-name'))
    self.assertEqual(
      a.assemble_line('p f1.A {d-other-name}'), format_comment('p f1.A 2','# 2=d-other-name'))

  def test_accumulator_lookup(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p {a-name}.A 8'), format_comment('p a1.A 8','# a1=a-name'))
    self.assertEqual(
      a.assemble_line('p {a-other-name}.A 8'), format_comment('p a2.A 8','# a2=a-other-name'))
    self.assertEqual(
      a.assemble_line('p 8 {a-other-name}.a'), format_comment('p 8 a2.a','# a2=a-other-name'))
    self.run_out(a, 'p {a-', '}.A 1', 18)

  def test_accumulator_reciever(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{r-name}i'), format_comment('p 1-1 a1.1i','# 1i=r-name'))
    self.assertEqual(
      a.assemble_line('p 1-1 a20.{t-name}i'),format_comment('p 1-1 a20.5i','# 5i=t-name'))
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{r-other-name}i'), format_comment('p 1-1 a1.2i','# 2i=r-other-name'))
    self.assertEqual(
      a.assemble_line('p a1.{r-other-name}i 2-2'), format_comment('p a1.2i 2-2','# 2i=r-other-name'))
    self.assertEqual(
      a.assemble_line('p {p-name} a1.{r-other-name}i'), format_comment('p 1-1 a1.2i','# 1-1=p-name, 2i=r-other-name'))
    self.assertEqual(
      a.assemble_line('p {p-name} {a-name}.{r-other-name}i'), format_comment('p 1-1 a1.2i','# 1-1=p-name, a1=a-name, 2i=r-other-name'))
    self.run_out(a, 'p 1-1 a1.{r-', '}i', 2)

    # we've run out of recievers on a1, but should still be plenty on a2
    self.run_out(a, 'p 1-1 a2.{r-', '}i', 4)

  def test_accumulator_transciever(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{t-name}i'), format_comment('p 1-1 a1.5i','# 5i=t-name'))
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{t-other-name}i'), format_comment('p 1-1 a1.6i','# 6i=t-other-name'))
    self.assertEqual(
      a.assemble_line('p a1.{t-other-name}o 2-2'), format_comment('p a1.6o 2-2','# 6o=t-other-name'))
    self.run_out(a, 'p 1-1 a1.{t-', '}i', 6)

    # we've run out of transcievers on a1, but should still be plenty on a2
    self.run_out(a, 'p 1-1 a2.{t-', '}i', 8)

  def test_accumulator_xceiver(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{x-name1}i'), format_comment('p 1-1 a1.1i','# 1i=x-name1'))
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{x-name2}i'), format_comment('p 1-1 a1.2i','# 2i=x-name2'))
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{x-name3}i'), format_comment('p 1-1 a1.3i','# 3i=x-name3'))
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{x-name4}i'), format_comment('p 1-1 a1.4i','# 4i=x-name4'))
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{x-name5}i'), format_comment('p 1-1 a1.5i','# 5i=x-name5'))
    self.run_out(a, 'p 1-1 a1.{x-', '}i', 7)

    # we've run out of xceivers on a1, but should still be plenty on a2
    self.run_out(a, 'p 1-1 a2.{x-', '}i', 12)

  def test_accumulator_inputs(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p 4 a1.{i-name}'), format_comment('p 4 a1.a','# a=i-name'))
    self.assertEqual(
      a.assemble_line('p 4 a1.{i-other-name}'), format_comment('p 4 a1.b','# b=i-other-name'))
    self.assertEqual(
      a.assemble_line('p 4 a1.{i-other-other-name}'), format_comment('p 4 a1.g','# g=i-other-other-name'))
    self.run_out(a, 'p 4 a1.{i-', '}', 2)

    # we've run out of inputs on a1, but should still be plenty on a2
    self.run_out(a, 'p 4 a2.{i-', '}', 5)

  def test_bad_accumulator_arg_error(self):
    a = Assembler()
    with self.assertRaises(SyntaxError):
      a.assemble_line('p a1.{r-name} 1-1')        # need i after receiver
    with self.assertRaises(SyntaxError):
      a.assemble_line('p a1.{t-name} 1-1')        # need i or o after transceiver
    with self.assertRaises(SyntaxError):
      a.assemble_line('s {a-name}.cc{i-name} 1')  # junk before {i-}, user probably meant {r-} here

  def test_reciever_output_error(self):
    a = Assembler()
    with self.assertRaises(SyntaxError):
      a.assemble_line('p a1.{r-name}o 1-1')  # receivers do not have outputs

  def test_switch_literal(self):
    a = Assembler()
    self.assertEqual(a.assemble_line('s cy.op 1a'), 's cy.op 1a')
    self.assertEqual(a.assemble_line('s i.io 1-1'), 's i.io 1-1')
    self.assertEqual(a.assemble_line('s a1.op5 a'), 's a1.op5 a')

  def test_switch_accumulator(self):
    a = Assembler()
    self.assertEqual(a.assemble_line('s {a-name}.op5 a'), format_comment('s a1.op5 a','# a1=a-name'))
    self.assertEqual(a.assemble_line('s {a-other-name}.op5 a'), format_comment('s a2.op5 a','# a2=a-other-name'))
    self.assertEqual(a.assemble_line('s a1.op{r-name} a'), format_comment('s a1.op1 a','# op1=r-name'))
    self.assertEqual(a.assemble_line('s a1.op{t-name} a'), format_comment('s a1.op5 a','# op5=t-name'))
    self.assertEqual(a.assemble_line('s a1.op1 {i-name}'), format_comment('s a1.op1 a','# a=i-name'))
    self.assertEqual(a.assemble_line('s a1.op2 {i-other-name}'), format_comment('s a1.op2 b','# b=i-other-name'))
    self.assertEqual(a.assemble_line('s {a-name}.op{t-name} {i-other-name}'), format_comment('s a1.op5 b','# a1=a-name, op5=t-name, b=i-other-name'))

  def test_non_accumulator_switch_input(self):
    a = Assembler()
    with self.assertRaises(SyntaxError):
      a.assemble_line('s cy.op {i-name}')

  def test_macro(self):
    a = Assembler()
    program = textwrap.dedent('''\
      defmacro test arg1 arg2  # for testing
      expansion $arg1 {$arg2}
      endmacro  # yay
      $test A {B}''')
    out = a.assemble('filename', program)
    self.assertEqual(out.splitlines(),
                     ["# (elided 'test' macro definition)",
                      '# $test A {B}',
                      'expansion A {B}'])

  def test_defmacro_missing_name(self):
    a = Assembler()
    with self.assertRaises(SyntaxError):
      a.assemble_line('defmacro')  # missing name

  def test_domacro_undef(self):
    a = Assembler()
    with self.assertRaises(SyntaxError):
      a.assemble_line('$undefined huh what')  # undefined macro

  def test_domacro_argcount(self):
    a = Assembler()
    a.macros['test'] = Macro(name='test', args=['arg1', 'arg2'], lines=[])
    with self.assertRaises(SyntaxError):
      out = a.assemble_line('$test A')


if __name__ == '__main__':
    unittest.main()
