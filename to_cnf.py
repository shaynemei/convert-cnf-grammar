from nltk import data
from nltk.grammar import is_terminal, Nonterminal, Production, CFG
import os, sys

def convert_hybrid(grammar):
    '''
    Convert rules in the form of [A -> 'b' C] where the rhs has both non-terminals and terminals
    into rules in the form of [A -> B C] & [B -> 'b'] with a dummy non-terminal B
    '''
    rules = grammar.productions()
    new_rules = []
    for rule in rules:
        lhs = rule.lhs()
        rhs = rule.rhs()
        # check for hybrid rules
        if rule.is_lexical() and len(rhs) > 1:
            new_rhs = []
            for item in rule.rhs():
                if is_terminal(item):
                    new_sym = Nonterminal(item)
                    new_rhs.append(new_sym)
                    # add new lexical rule with dummy lhs nonterminal
                    new_rules.append(Production(new_sym, (item,)))
                else:
                    new_rhs.append(item)
            # add converted mixed rule with only non-terminals on rhs
            new_rules.append(Production(lhs, tuple(new_rhs)))
        else:
            new_rules.append(rule)
    
    new_grammar = CFG(grammar.start(), new_rules)
    
    return new_grammar

def convert_unit(grammar):
    '''
    Convert unitary rules in the form of [A -> B] where the rhs has one non-terminal
    by eliminating intermediate unitary rules and promoting the final lexical rule, e.g. [B -> 'b'] => [A -> 'b']
    or stop at an intermediate rule with only non-terminals on the rhs like [B -> C D] => [A -> C D]
    '''
    
    rules = grammar.productions()
    new_rules = []
    unit_rules = []
    for rule in rules:
        # check for unit rules
        if rule.is_nonlexical() and len(rule) == 1:
            unit_rules.append(rule)
        else:
            new_rules.append(rule)
    
    # following each unit rule and find the final terminal
    while unit_rules:
        rule = unit_rules.pop(0)
        lhs = rule.lhs()
        rhs = rule.rhs()
        # find rules that can derive the rhs to something else
        for cascade_rule in grammar.productions(lhs=rhs[0]):
            temp_rule = Production(lhs, cascade_rule.rhs())
            if cascade_rule.is_lexical() or len(cascade_rule) > 1:
                new_rules.append(temp_rule)
            else:
                unit_rules.append(temp_rule)
                
    new_grammar = CFG(grammar.start(), new_rules)
    
    return new_grammar

def convert_long(grammar):
    '''
    Convert non-binary rules in the form of [A -> B C D], where the rhs has more than 2 non-terminals
    into binarised rules in the form of [A -> B_C D] & [B_C -> B C] witha dummy non-terminal B_C
    '''
    
    rules = grammar.productions()
    new_rules = []
    long_rules = []
    for rule in rules:
        if len(rule.rhs()) > 2:
            long_rules.append(rule)
        else:
            new_rules.append(rule)
    
    while long_rules:
        rule = long_rules.pop(0)
        lhs = rule.lhs()
        rhs = rule.rhs()
        new_rhs = []
        for i in range(0, len(rhs) - 1, 2):
            new_sym = Nonterminal(f"{rhs[i].symbol()}_{rhs[i + 1].symbol()}")
            new_rules.append(Production(new_sym, (rhs[i], rhs[i+1])))
            new_rhs.append(new_sym)
        # case: odd number of non-terminals on rhs
        if len(rhs) % 2 == 1:
            new_rhs.append(rhs[-1])
            
        new_rule = Production(lhs, tuple(new_rhs))
        # continue binarisation if rhs still has more than 2 non-terminals
        if len(new_rhs) > 2:
            long_rules.append(new_rule)
        else:
            new_rules.append(new_rule)
    
    new_grammar = CFG(grammar.start(), new_rules)
    
    return new_grammar

def toCNF(grammar):
    '''
    Convert a CFG to a weakly equivalent grammar in CNF in 3 steps:
    Step 1: for hybrid rules, convert terminals to dummy non-terminals
    Step 2: for non-lexical unitary rules, follow rhs down to terminals or non-unitary non-terminals
    Step 3: binarise all resulting rules

    '''
    return convert_long(convert_unit(convert_hybrid(grammar)))

if __name__ == "__main__":
    inp =sys.argv[1]
    out = sys.argv[2]
    grammar = data.load(f"{inp}")
    cnf_grammar = toCNF(grammar)
    with open(out, 'w') as f:
        f.write("% start SIGMA\n")
        for rule in cnf_grammar.productions():
            f.write(str(rule))
            f.write("\n")








