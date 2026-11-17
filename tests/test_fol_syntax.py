import unittest
from bns_fol.syntax.terms import Variable, Constant
from bns_fol.syntax.predicates import Atom, Literal
from bns_fol.syntax.formulas import AndFormula, OrFormula, ImpliesFormula, ForAll

class TestFOLSyntax(unittest.TestCase):
    def test_terms(self):
        v_x = Variable("x")
        c_a = Constant("A")
        self.assertEqual(str(v_x), "x")
        self.assertEqual(str(c_a), "A")
        self.assertEqual(c_a.to_latex(), r"\text{A}")

    def test_predicates_and_literals(self):
        v_x = Variable("x")
        v_y = Variable("y")
        atom = Atom("CausesDeath", v_x, v_y)
        self.assertEqual(str(atom), "CausesDeath(x, y)")

        lit_pos = Literal(atom)
        self.assertFalse(lit_pos.is_negated)
        self.assertEqual(str(lit_pos), "CausesDeath(x, y)")

        lit_neg = lit_pos.negate()
        self.assertTrue(lit_neg.is_negated)
        self.assertEqual(str(lit_neg), "¬CausesDeath(x, y)")
        self.assertEqual(lit_neg.to_ascii(), "~CausesDeath(x, y)")

    def test_formulas(self):
        v_x = Variable("x")
        v_y = Variable("y")
        l1 = Literal(Atom("CausesDeath", v_x, v_y))
        l2 = Literal(Atom("IntentionToCauseDeath", v_x, v_y))
        conc = Literal(Atom("PrimaFacieMurder", v_x, v_y))

        conj = AndFormula(l1, l2)
        impl = ImpliesFormula(conj, conc)
        forall = ForAll([v_x, v_y], impl)

        self.assertIn("CausesDeath(x, y)", str(forall))
        self.assertIn("∧", str(forall))
        self.assertIn("→", str(forall))
        self.assertIn(r"\forall x, y", forall.to_latex())

if __name__ == "__main__":
    unittest.main()
