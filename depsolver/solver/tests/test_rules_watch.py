import unittest

from ..rules_watch_graph \
    import \
        RuleWatchChain

class TestRuleChain(unittest.TestCase):
    def test_simple(self):
        chain = RuleWatchChain()
        chain.unshift(1)
        chain.unshift(2)
        chain.unshift(3)

        self.assertEqual(list(chain), [3, 2, 1])

    def test_remove_simple(self):
        chain = RuleWatchChain()
        chain.unshift(1)
        chain.unshift(2)
        chain.unshift(3)

        chain.remove()
        self.assertEqual(list(chain), [2, 1])

    def test_remove_middle(self):
        chain = RuleWatchChain()
        chain.unshift(1)
        chain.unshift(2)
        chain.unshift(3)

        chain.rewind()
        chain.next()
        chain.remove()
        self.assertEqual(list(chain), [3, 1])
