"""KiCad PCB source-side pad/net inventory for pinned open-board acceptance.

This reads the original board text. It does NOT assert that LabWired imported
its pads or simulated any component. Hashing each reference/pad/net tuple gives
later importer runs an independent connectivity oracle.
"""
import hashlib
import json


def tokens(source: str):
    """Strict KiCad s-expression tokenizer, including quoted strings/comments."""
    i = 0
    while i < len(source):
        char = source[i]
        if char.isspace():
            i += 1
        elif char == '#':
            stop = source.find('\n', i)
            i = len(source) if stop < 0 else stop + 1
        elif char in '()':
            yield char
            i += 1
        elif char == '"':
            i += 1
            value = []
            while i < len(source):
                char = source[i]
                if char == '"':
                    i += 1
                    yield ''.join(value)
                    break
                if char == '\\':
                    i += 1
                    if i >= len(source):
                        raise ValueError('truncated KiCad quoted escape')
                    char = {'n': '\n', 'r': '\r', 't': '\t'}.get(source[i], source[i])
                value.append(char)
                i += 1
            else:
                raise ValueError('unterminated KiCad quoted string')
        else:
            start = i
            while i < len(source) and not source[i].isspace() and source[i] not in '()"':
                i += 1
            if i == start:
                raise ValueError('unexpected KiCad token')
            yield source[start:i]


def parse(source: str):
    """Parse balanced s-expressions without evaluating input as code."""
    roots = []
    stack = []
    for token in tokens(source):
        if token == '(':
            node = []
            if stack:
                stack[-1].append(node)
            else:
                roots.append(node)
            stack.append(node)
        elif token == ')':
            if not stack:
                raise ValueError('unmatched KiCad closing parenthesis')
            stack.pop()
        else:
            if not stack:
                raise ValueError('token outside KiCad expression')
            stack[-1].append(token)
    if stack or len(roots) != 1 or roots[0][:1] != ['kicad_pcb']:
        raise ValueError('not a complete KiCad PCB expression')
    return roots[0]


def direct_nodes(node, tag):
    return (child for child in node if isinstance(child, list) and child and child[0] == tag)


def source_topology(source: bytes):
    """Count source footprints and pads; hash reference/pad/net multiset.

    Unconnected pads are retained with an empty net name. Numbers may repeat
    when a footprint uses several physical pads for one logical pin.
    """
    root = parse(source.decode('utf-8-sig'))
    footprints = list(direct_nodes(root, 'footprint'))
    pads = []
    references = set()
    for footprint in footprints:
        ref = next((p[2] for p in direct_nodes(footprint, 'property')
                    if len(p) >= 3 and p[1] == 'Reference'), None)
        if ref is None:
            ref = next((p[2] for p in direct_nodes(footprint, 'fp_text')
                        if len(p) >= 3 and p[1] == 'reference'), None)
        if not isinstance(ref, str) or not ref or ref in references:
            raise ValueError(f'missing or repeated footprint reference: {ref!r}')
        references.add(ref)
        for pad in direct_nodes(footprint, 'pad'):
            if len(pad) < 3 or not isinstance(pad[1], str):
                raise ValueError(f'invalid pad on {ref}')
            nets = list(direct_nodes(pad, 'net'))
            if len(nets) > 1:
                raise ValueError(f'multiple nets on {ref}.{pad[1]}')
            net = nets[0][-1] if nets and len(nets[0]) > 1 else ''
            # KiCad versions may emit (net 0 "") or omit net on an NC pad.
            if net == '0':
                net = ''
            if not isinstance(net, str):
                raise ValueError(f'invalid net on {ref}.{pad[1]}')
            pads.append((ref, pad[1], net))
    nets = {net for _, _, net in pads if net}
    encoded = json.dumps(sorted(pads), ensure_ascii=False, separators=(',', ':')).encode()
    return {
        'footprints': len(footprints),
        'pads': len(pads),
        'pads_with_nets': sum(bool(net) for _, _, net in pads),
        'pads_without_nets': sum(not net for _, _, net in pads),
        'distinct_pad_nets': len(nets),
        'pad_net_sha256': hashlib.sha256(encoded).hexdigest(),
    }
