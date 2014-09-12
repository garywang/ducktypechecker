import ast
from collections import deque

class Node(object):
    next_id = 0

    def __init__(self):
        self.preds = []
        self.succs = []
        self.id = Node.next_id
        Node.next_id += 1

    def link(self, next):
        self.succs.append(next)
        next.preds.append(self)

    """def __str__(self):
        return '%s: %r, next: %s' % (self.id, self, self.succs)"""

class Nop(Node):
    def __repr__(self):
        return 'NopNode(%s)' % self.id

class Branch(Node):
    def __init__(self, cond):
        super(Branch, self).__init__()
        self.cond = cond

    def __repr__(self):
        return 'BranchNode(%s, %s)' % (self.id, ast.dump(self.cond))

class Statement(Node):
    """A Node for a statement that doesn't change the control flow."""
    def __init__(self, stmt):
        super(Statement, self).__init__()
        self.stmt = stmt

    def __repr__(self):
        return 'StatementNode(%s, %s)' % (self.id, ast.dump(self.stmt))

def walk(start):
    visited = set()
    nodes = []
    def visit(node):
        visited.add(node)
        for succ in reversed(node.succs):
            if succ not in visited:
                visit(succ)
        nodes.append(node)
    visit(start)
    nodes.reverse()
    return nodes

def dump(start):
    nodes = walk(start)
    index = {node: n for n, node in enumerate(nodes)}

    for node in nodes:
        if len(node.preds) > 1:
            print '   next: [%s]' % index[node]
            print '---'

        print '%s: %s' % (index[node], node)

        if len(node.succs) == 0:
            print '---'
        elif index[node.succs[0]] == index[node] + 1:
            if len(node.succs) > 1:
                print '   next: %s' % [index[succ] for succ in node.succs]
        else:
            print '   next: %s' % [index[succ] for succ in node.succs]
            print '---'
        



class Block(object):
    def __init__(self, first=None, last=None):
        if first is None:
            first = Nop()
        if last is None:
            last = first
        if isinstance(first, Block):
            first = first.first
        if isinstance(last, Block):
            last = last.last
        self.first = first
        self.last = last

    def __repr__(self):
        return 'Block(%s, %s)' % (self.first.id, self.last.id)

def link(prev, next):
    if isinstance(prev, Node):
        prev = Block(prev)
    if isinstance(next, Node):
        next = Block(next)
    prev.last.link(next.first)
    return Block(prev.first, next.last)

class CfgBuilder(object):

    def __init__(self):
        pass

    def convert_block(self, stmts):
        """Given a list of ast.stmt, converts it to a Block."""
        if len(stmts) == 0:
            return Block()
        subblocks = [self.convert_statement(stmt) for stmt in stmts]
        if len(stmts) > 1:
            for prev, next in zip(subblocks[:-1], subblocks[1:]):
                link(prev, next)
        return Block(subblocks[0].first, subblocks[-1].last)

    def convert_if(self, stmt):
        """Given an ast.If, converts it to a Block."""
        head = Branch(stmt.test)
        tail = Nop()

        true_branch = self.convert_block(stmt.body)
        link(head, true_branch)
        link(true_branch, tail)

        if len(stmt.orelse) > 0:
            false_branch = self.convert_block(stmt.orelse)
            link(head, false_branch)
            link(false_branch, tail)
        else:
            link(head, tail)

        return Block(head, tail)

    def convert_while(self, stmt):    
        """Given an ast.While, converts it to a Block."""
        head = Branch(stmt.test)
        tail = Nop()
        body = self.convert_block(stmt.body) # TODO: add break and continue targets
        orelse = self.convert_block(stmt.orelse)

        link(head, body)
        link(head, orelse)
        link(body, head)
        link(orelse, tail)

        return Block(head, tail)

    def convert_statement(self, stmt):
        """Given an ast.stmt, converts it to a Block."""
        if isinstance(stmt, ast.If):
            return self.convert_if(stmt)
        elif isinstance(stmt, ast.While):
            return self.convert_while(stmt)
        elif isinstance(stmt, (ast.Assign,
                               ast.AugAssign,
                               ast.Delete,
                               ast.Print,
                               ast.Expr)):
            return Block(Statement(stmt))
        elif isinstance(stmt, ast.Pass):
            return Block()
        else:
            raise NotImplementedError("Statement %s not yet implemented" % type(stmt))
