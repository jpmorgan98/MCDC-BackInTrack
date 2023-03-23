import numpy as np
from os.path import getmtime, exists
from os      import mkdir
from numba import njit, cuda
import numba
import re
import itertools

def fn_arg_ano_list( func ):
    result = []
    for arg,ano in func.__annotations__.items():
        if( arg != 'return' ):
            result.append(ano)
    return result

def fn_arg_ano( func ):
    return tuple( x for x in fn_arg_ano_list(func) )
            
def assert_fn_res_ano( func, res_type ):
    if 'return' in func.__annotations__:
        res_ano = func.__annotations__['return']
        if res_ano != res_type :
            arg_str  = str(fn_arg_ano(func))
            ano_str  = arg_str + " -> " + str(res_ano)
            cmp_str  = arg_str + " -> " + str(res_type)
            err_str  = "Annotated function type '" + ano_str               \
            + "' does not match the type deduced by the compiler '"        \
            + cmp_str + "'\nMake sure the definition of the function '"    \
            + func.__name__ + "' results in a return type  matching its "  \
            + "annotation when supplied arguments matching its annotation."
            raise(TypeError(err_str))
            

def global_ptx( func ):
    ptx, res_type = cuda.compile_ptx(func,fn_arg_ano(func))
    assert_fn_res_ano(func, res_type)
    return ptx

def device_ptx( func ):
    ptx, res_type = cuda.compile_ptx(func,fn_arg_ano(func),device=True)
    assert_fn_res_ano(func, res_type)
    return ptx, res_type

def func_defn_time(func):
    return getmtime(func.__globals__['__file__'])




def remove_ptx_comments(ptx_text):
    space = ' \t\r\n'
    ptx_text = "\n".join([ line.lstrip(space) for line in ptx_text.splitlines() if len(line.lstrip(space)) != 0 ])
    
    filtered = []
    start_split = ptx_text.split("/*")
    for index, entry in enumerate(start_split) :
        end_split = entry.split("*/")
        if index == 0 :
            if len(end_split) != 1 :
                raise AssertionError("PTX has an unmatched comment block end")
            filtered.append(end_split[0])
        elif len(end_split) !=2 :
            raise AssertionError("PTX has an unmatched comment block end")
        else :
            filtered.append(end_split[1])

    ptx_text = "".join(filtered)

    ptx_text = "\n".join([ line.lstrip(space) for line in ptx_text.splitlines() if not line.lstrip(space).startswith("//") ])

    ptx_text = "\n".join([ line.split("//")[0] for line in ptx_text.splitlines() ])
    
    return ptx_text

def parse_braks(ptx_text,paren_pairs,closer=None):
    seq = []
    limit = len(ptx_text)
    start = 0
    index = 0
    while index < limit :
        character = ptx_text[index]
        if character == closer :
            seq.append(ptx_text[start:index])
            #print("------------")
            #print(seq)
            return ( closer, seq ), index + 1
        for open,close in paren_pairs :
            if character == open :
                seq.append(ptx_text[start:index-1])
                index += 1
                sub_seq, delta = parse_braks(ptx_text[index:limit],paren_pairs,close)
                seq.append(sub_seq)
                index += delta
                start = index
        index += 1
    seq.append(ptx_text[start:index])
    #print("------------")
    #print(seq)
    return ( closer, seq ), index
    
                


def parse_sep(ptx_brak_tree, sep):
    closer, seq = ptx_brak_tree
    new_seq = []
    sep_found = False
    sep_seq = []
    for sub_seq in seq :
        if isinstance(sub_seq,str) :
            split_seq = sub_seq.split(sep)
            length = len(split_seq)
            if length == 1 :
                sep_seq.append(split_seq[0])
                #print("\n??????\n")
                #print(sub_seq)
                #print(sep_seq)
            elif length > 1 :
                sep_found = True
                sep_seq.append(split_seq[0])
                new_seq.append((sep,sep_seq))
                sep_seq = [split_seq[-1]]
                [new_seq.append((sep,[split])) for split in split_seq[1:-1]]
        elif sub_seq[0] == '}':
            new_seq += sep_seq
            sep_seq = []
            new_seq.append(parse_sep(sub_seq,sep))
        else :
            sep_seq.append(parse_sep(sub_seq,sep))
    if sep_found :
        new_seq.append((sep,sep_seq))
        return (closer,new_seq)
    else :
        new_seq += sep_seq
        return (closer,new_seq)


def parse_tok(parse_tree):
    closer, seq = parse_tree
    new_seq = []
    for chunk in seq:
        if isinstance(chunk,str):
            sub_seq = chunk.split()
            if len(sub_seq) > 0:
                new_seq.append((' ',sub_seq))
        else:
            sub_tree = parse_tok(chunk)
            if sub_tree[0] != ' ' or len(sub_tree[1]) != 0:
                new_seq.append(parse_tok(chunk))
    return (closer,new_seq)



def parse_ptx(ptx_text):
    ptx_text = remove_ptx_comments(ptx_text)
    #print(ptx_text)
    braks = [ ('(',')'), ('[',']'), ('{','}'), ('<','>') ]
    parse_tree, _ = parse_braks(ptx_text,braks)
    seperators  = [ ';' , ',', ':' ]
    for sep in seperators:
        parse_tree = parse_sep(parse_tree,sep)
        #print(parse_tree)
    parse_tree = parse_tok(parse_tree)
    #print("\n----\n")
    #print(parse_tree)
    return parse_tree


def delim_match(chunk_list,delim_list):
    if len(delim_list) > len(chunk_list):
        return False
    for index, delim in enumerate(delim_list):
        if chunk_list[index][0] != delim:
            return False
    return True




def extract_regex(parse_tree,regex):
    _, chunks = parse_tree
    result = []
    for index, chunk in enumerate(chunks):
        if isinstance(chunk,str):
            continue
        sep, content = chunk
        if sep != "ptx":
            result += extract_regex((sep,content),regex)
            continue
        for match in re.finditer(regex,content):
            result.append((match, index, chunks))
    return result


def find_extern_funcs(parse_tree):
    #.extern .func (.param .type func_retval0) func_name (.param .type param_name, ... )
    #(name,[(par_kind,par_name),(par_kind,par_name), ()...])
    result = []
    extern_regex = r'.extern\s+.func\s*\(\s*.param\s\.+\w+\s+\w+\s*\)\s*(?P<name>\w+)\((?P<params>(\s*.param\s+\.\w+\s+\w+\s*)(,\s*.param\s+\.\w+\s+\w+\s*)*)\)'
    param_regex = r'\s*.param\s+(?P<type>\.\w+)\s+(?P<name>\w+)\s*'
    for match, _, _ in extract_regex(parse_tree,extern_regex):
        params = [(p['type'],p['name']) for p in re.finditer(param_regex,match['params'])]
        result.append((match['name'],params))
    return result


def find_visible_funcs(parse_tree):
    #.extern .func (.param .type func_retval0) func_name (.param .type param_name, ... )
    #(name,[(par_kind,par_name),(par_kind,par_name), ()...])
    result = []
    extern_regex = r'\.visible\s+\.func\s*\(\s*\.param\s+\.\w+\s+\w+\s*\)\s*(?P<name>\w+)\((?P<params>(\s*\.param\s+\.\w+\s+\w+\s*)(,\s*.param\s+\.\w+\s+\w+\s*)*)\)'
    param_regex = r'\s*\.param\s+(?P<type>\.\w+)\s+(?P<name>\w+)\s*'
    for match, index, context in extract_regex(parse_tree,extern_regex):
        params = [(p['type'],p['name']) for p in re.finditer(param_regex,match['params'])]
        result.append((match['name'],params,context[index+1]))
    return result


def replace(parse_tree,rep_list,whole=False):
    if isinstance(parse_tree,str):
        for targ, dest in rep_list:
            pattern = targ
            if whole:
                pattern = "\\b" + pattern + "\\b"
            parse_tree = re.sub(pattern,dest,parse_tree)
        return parse_tree
    else:
        sep, content = parse_tree
        if sep == "ptx":
            return (sep, replace(content,rep_list,whole))
        new_content = []
        for chunk in content:
            new_content.append(replace(chunk,rep_list,whole))
        return (sep,new_content)
        

def has_curly_block(parse_tree):
    if isinstance(parse_tree,str):
        return False
    sep, content = parse_tree
    if sep == '}':
        return True
    for chunk in content:
        if has_curly_block(chunk):
            return True
    return False

def has_colon(parse_tree):
    if isinstance(parse_tree,str):
        return False
    sep, content = parse_tree
    if sep == ':':
        return True
    for chunk in content:
        if has_colon(chunk):
            return True
    return False

def linify_tree(parse_tree):
    if isinstance(parse_tree,str):
        return parse_tree
    sep, content = parse_tree
    if sep ==';' and not has_curly_block(parse_tree):
        return  ("ptx",stringify_tree(parse_tree)) 

    hit_curly   = False
    hit_line    = False
    line        = []
    new_content = []
    for chunk in content:
        if isinstance(chunk,str):
            new_content.append(chunk)
            continue
        chunk = linify_tree(chunk)
        sub_sep, sub_con = chunk
        if sub_sep == "ptx":
            hit_line = True
            split = sub_con.split(':')
            for index, sub_chunk in enumerate(split):
                if index != 0:
                    sub_chunk = sub_chunk[1:]
                if index != len(split)-1 :
                    new_content.append(("ptx",sub_chunk+":\n"))
                else:
                    new_content.append(("ptx",sub_chunk))
        elif sub_sep == '}':
            hit_curly = True
            new_content.append(("ptx",stringify_tree((None,line))+"\n"))
            line = []
            new_content.append((sub_sep,sub_con))
        else:
            line.append((sub_sep,sub_con))
    if len(line) != 0:
        if (hit_curly or hit_line):
            new_content.append(("ptx",stringify_tree((None,line))+"\n"))
        else:
            new_content += line
    return (sep,new_content)


def stringify_tree(parse_tree,last=False,depth=0):
    brak_list = [')',']','}','>']
    brak_map  = {')':'(',']':'[','}':'{','>':'<'}
    sep_list  = [',',';',':']

    tabs = '\t'*depth

    if isinstance(parse_tree,str):
        return " " + parse_tree
    else:
        sep, content = parse_tree

        if sep == "cuda":
            return tabs + content
        
        if sep == "ptx":
            return tabs + "asm volatile (\"" + content.rstrip() + "\");\n"
 
        if sep == ' ':
            return "\t".join(content)

        sub_depth = depth
 
        result = ""

        if sep in brak_list:
            if sep == '}':
                sub_depth += 1
                result    += tabs + "asm volatile (\"" + str(brak_map[sep]) + "\");\n"
            else:
                result += str(brak_map[sep])

        for index, chunk in enumerate(content):
            sub_last = (index == (len(content)-1))
            result += stringify_tree(chunk,sub_last,sub_depth)

        if sep in brak_list:
            if sep == '}':
                result    += tabs + "asm volatile (\"" + str(sep) + "\");\n"
            else:
                result += str(sep)

        elif (sep in sep_list) and not last:
            result += str(sep)
            if sep == ';' or sep == ':':
                result += '\n' + tabs
            else:
                result += '\t'
        return result





def strip_ptx(ptx_text):
    ignore_list = [ "//", ".version", ".target" , ".address_size", ".common" ]
    # get rid of empty lines and leading whitespace
    space = ' \t\r\n'
    ptx_text = "\n".join([ line.lstrip(space) for line in ptx_text.splitlines() if len(line.lstrip(space)) != 0 ])
    # get rid of comments and other ptx lines we don't care about
    for entry in ignore_list:
        ptx_text = "\n".join([ line for line in ptx_text.splitlines() if not line.lstrip(space).startswith(entry) ])
    return ptx_text




def replace_call_params(context,call_idx,ret,signature,params,temp_count):
    kind_map = {
        "u8":"h", "u16":"h", "u32":"r", "u64":"l",
        "s8":"h", "s16":"h", "s32":"r", "s64":"l",
        "b8":"h", "b16":"h", "b32":"r", "b64":"l",
        "f32":"f", "f64":"d",
    }

    params.append(ret)

    for id, param in enumerate(params):
        #print(param)
        decl_regex = r"\.param\s+\.\w+\s+"+param+r"\s*;"
        move_regex = r"st\.param\.(?P<kind>\w+)\s*\[\s*"+param+r"\s*(\+\s*[0-9]+\s*)?\]\s*,\s*(?P<src>\w+)\s*;"
        if param == ret:
            move_regex = r"ld\.param\.(?P<kind>\w+)\s*(?P<dst>\w+)\s*,\s*\[\s*"+param+r"\+0\]\s*;"

        start = min(call_idx+2,len(context))
        found_decl = False
        found_move = False
        for line_idx in range(start,-1,-1):
            if found_decl and found_move:
                break
            if isinstance(context[line_idx],str):
                continue
            if context[line_idx][0] != 'ptx':
                continue
            #print(context[line_idx][1])
            if re.match(decl_regex,context[line_idx][1]) != None:
                found_decl = True
                if param == ret:
                    context[line_idx] = ('cuda', "//"+context[line_idx][1])
                else:
                    line = '{kind} _param_{id};\n'
                    line = line.format(kind=str(signature[id]),id=temp_count+id)
                    context[line_idx] = ('cuda',line)
                continue
            move_match = re.match(move_regex,context[line_idx][1])
            if move_match != None:
                found_move = True
                kind = move_match['kind']
                if param == ret:
                    dst = move_match['dst']
                    line = 'asm volatile(\"cvt.{kind}.{kind} {dst}, 0;\");\n'
                    line = line.format(kind=kind,dst=dst)
                    context[line_idx] = ('cuda',line)
                else:
                    src  = move_match['src']
                    line = 'asm volatile(\"cvt.{kind}.{kind} %0, {src};\" : \"={kid}\"(_param_{id}) : );\n'
                    line = line.format(kind=kind,src=src,id=temp_count+id,kid=kind_map[kind])
                    context[line_idx] = ('cuda',line)
    return temp_count + len(params)-1


def replace_call( parse_tree, mapping, temp_count, context=[] ):
    repl_fn, repl_name = mapping
    src_list = []
    ret  = None
    call_regex = r"call\.uni\s*\(\s*(?P<ret>\w+)\s*\)\s*,\s*"+repl_fn.name+r"\s*,\s*\((?P<params>\s*\w+\s*(,\s*\w+\s*)*)\)\s*;\s*"
    param_regex = r'\b(?P<name>\w+)\b'
    for match, index, context in extract_regex(parse_tree,call_regex):
        #print(match)

        ret         = match['ret']
        params      = [p['name'] for p in re.finditer(param_regex,match['params'])]
        #print(params)
        signature   = [ str(repl_fn.sig.return_type) + "*" ] + [ str(arg) for arg in repl_fn.sig.args ]

        old_tc = temp_count
        temp_count = replace_call_params(context,index,ret,signature,params,temp_count)
        arg_str = ",".join([ "_param_"+str(x) for x in range(old_tc,temp_count)])

        context[index] = ('cuda', repl_name + "(" + arg_str + ");\n" )
    return temp_count




def replace_externs( parse_tree, function_map ):
    temp_count = 0
    for mapping in function_map.items():
        temp_count = replace_call(parse_tree,mapping,temp_count)



def replace_fn_params( parse_tree, params, has_return ):
    kind_map = {
        "u8":"h", "u16":"h", "u32":"r", "u64":"l",
        "s8":"h", "s16":"h", "s32":"r", "s64":"l",
        "b8":"h", "b16":"h", "b32":"r", "b64":"l",
                                "f32":"f", "f64":"d",
    }
    param_regex = r"ld\.param\.(?P<kind>\w+)\s+(?P<dst>\w+)\s*,\s*\[(?P<name>\w+)\]\s*;"

    for match, index, context in extract_regex(parse_tree,param_regex):
        kind = match['kind']
        dst  = match['dst']
        name = match['name']
        #print(name)

        if name not in params:
            continue

        line = 'asm volatile (\"cvt.{kind}.{kind} {dst}, %0\" : : \"{kid}\"({name}) );\n'
        line = line.format(kind=kind,dst=dst,name=name,kid=kind_map[kind])
        context[index] = ('cuda',line)
    
    return_regex = r"st\.param\.(?P<kind>\w+)\s*\[func_retval0\+0\]\s*,\s*(?P<src>\w+)\s*;"
    for match, index, context in extract_regex(parse_tree,return_regex):
        if has_return:
            kind = match['kind']
            src  = match['src']
            line = 'asm volatile (\"cvt.{kind}.{kind} %0, {src}\" : \"={kid}\"(result) : );\n'
            line = line.format(kind=kind,src=src,kid=kind_map[kind])
            context[index] = ('cuda',line )
        else:
            context[index] = ('cuda',"//"+context[index][1])



def fix_returns(parse_tree):

    return_regex = r"ret\s*;"

    for _, index, context in extract_regex(parse_tree,return_regex):
        context[index] = ('ptx',"bra: _RETURN;")





def inlined_device_ptx( func, function_map):
    arg_types   = fn_arg_ano_list(func)
    ptx_text, res_type = device_ptx(func)
    parse_tree  = parse_ptx(ptx_text)
    line_tree   = linify_tree(parse_tree)
    visible_fns = find_visible_funcs(line_tree)
    #print(stringify_tree(linify_tree(parse_tree)))

    if len(visible_fns) == 0:
        raise AssertionError("PTX for user-defined function contains no '.visible .func'")
    elif len(visible_fns) > 1:
        raise AssertionError("PTX for user-defined function contains multiple '.visible .func'")


    name, params, body = visible_fns[0]

    whole_tf_list = []
    inner_tf_list = [("%","_")]
    par_types     = []

    whole_tf_list.append((name,func.__name__))

    targ_par_names  = fn_arg_ano_list(func)
    #print(targ_par_names)

    for index, param in enumerate(params):
        par_name = param[1]
        whole_tf_list.append((par_name,"fn_param_"+str(index)))

    body = replace(body,whole_tf_list,whole=True)
    body = replace(body,inner_tf_list,whole=False)

    replace_externs(body,function_map)
 
    has_return = 'return' in func.__annotations__
 
    replace_fn_params(body,["fn_param_"+str(index) for index in range(len(params))], has_return)
    fix_returns(body)
    body[1].append(('ptx',"_RETURN:"))
    cuda_body = stringify_tree(body,False,2)

    return cuda_body



def map_type_name(type_map,kind):
    primitives = {
        bool       : "bool",
        np.bool8   : "bool", 
        np.uint8   : "uint8_t", 
        np.uint16  : "uint16_t", 
        np.uint32  : "uint32_t", 
        np.uint64  : "uint64_t", 
        np.int8    : "int8_t", 
        np.int16   : "int16_t", 
        np.int32   : "int32_t", 
        np.int64   : "int64_t", 
        np.float32 : "float", 
        np.float64 : "double" 
    }

    print(numba.types.Literal)
    print(type(numba.types.Literal))
    print(type(kind))
    print(kind)

    if kind in primitives:
        return primitives[kind]
    elif isinstance(kind,numba.types.abstract.Literal):
        return map_type_name(type_map,type(kind._literal_value))
    elif isinstance(kind,numba.types.Integer):
        result = "int"
        if not kind.signed :
            result = "u" + result
        result += str(kind.bitwidth)
        return result + "_t"
    elif isinstance(kind,numba.types.Float):
        return "float" + str(kind.bitwidth)
    elif isinstance(kind,numba.types.Boolean):
        return "bool"
    elif isinstance(kind,numba.types.Record):
        return type_map[kind] + "*"
    else:
        raise RuntimeError("Unrecognized type '"+str(kind)+"'")


def harm_template_func(func,template_name,function_map,type_map):

    print(func.__name__)

    return_type = "void"
    if 'return' in func.__annotations__:
        return_type = map_type_name(type_map, func.__annotations__['return'])

    param_list  = fn_arg_ano_list(func)
    param_list  = [ map_type_name(type_map,kind) for kind in param_list ]
    arg_text    = ", ".join([ kind+" fn_param_"+str(idx+1) for (idx,kind) in enumerate(param_list)])

    if len(param_list) > 0:
        arg_text  = ", " + arg_text

    code = "\ttemplate<typename PROGRAM>\n"                                              \
	     + "\t__device__ static "+return_type+" "+template_name+"(PROGRAM prog" + arg_text + ") {\n"

    if return_type != "void":
        code += "\t\t"+return_type+" result;\n"
        code += "\t\t"+return_type+" *fn_param_0;\n"

    code += inlined_device_ptx(func,function_map)
    if return_type != "void":
        code += "\t\treturn result;\n"
    code += "\t}\n"

    return code


def pascal_case(name):
    return name.replace("_", " ").title().replace(" ", "")


def harm_async_func(func, function_map, type_map):
    return_type = "void"
    if 'return' in func.__annotations__:
        return_type = map_type_name(type_map, func.__annotations__['return'])
    func_name = str(func.__name__)

    struct_name = pascal_case(func_name)
    param_list  = fn_arg_ano_list(func)
    param_list  = [ map_type_name(type_map,kind) for kind in param_list ]
    param_text  = ", ".join(param_list)

    code = "struct " + struct_name + " {\n"                                              \
	     + "\tusing Type = " + return_type + "(*)(" + param_text + ");\n"                \
         + harm_template_func(func,"eval",function_map,type_map)                         \
         + "};\n"

    return code



def record_to_struct(record_kind,record_name,type_map):
    result = "struct " + record_name + " {\n"
    for name, kind in record_kind.members:
        result += "\t" + map_type_name(type_map,kind) + " " + name + ";\n"
    result += "};\n"
    return result



def harmonize(spec_name, function_map, type_map, state_spec, base_fns, async_fns):
    dev_state, grp_state, thd_state = state_spec
    init, final, source = base_fns
    type_defs = ""
    for kind, name in type_map.items():
        type_defs += record_to_struct(kind,name,type_map)

    async_defs = ""
    for func in async_fns:
        async_defs += harm_async_func(func,function_map,type_map)

    metaparams = {
        "STASH_SIZE" : 8,
        "FRAME_SIZE" : 8191,
        "POOL_SIZE"  : 8191,
    }

    meta_defs = "".join(["\tstatic const size_t "+name+" = "+str(value) +";\n" for name,value in metaparams.items()])

    union_def = "\ttypedef OpUnion<"+",".join([pascal_case(str(func.__name__)) for func in async_fns])+"> OpSet;\n"

    state_defs = "\ttypedef "+map_type_name(type_map,dev_state)+" DeviceState;\n" \
               + "\ttypedef "+map_type_name(type_map,grp_state)+" GroupState;\n"  \
               + "\ttypedef "+map_type_name(type_map,thd_state)+" ThreadState;\n"


    spec_def = "struct " + spec_name + "{\n"                                 \
             + meta_defs + union_def + state_defs                            \
             + harm_template_func(init  ,"initialize",function_map,type_map) \
             + harm_template_func(final ,"finalize"  ,function_map,type_map) \
             + harm_template_func(source,"make_work" ,function_map,type_map) \
             + "};"

    return type_defs + async_defs + spec_def

    






def cpu_func_adapt(func):
    return njit(     func, cache=True)

def cpu_ctrl_adapt(ctrl_unit,func_list):
    return njit(ctrl_unit, cache=True)


def gpu_func_adapt(func):
    return cuda.jit(    func,  device=True, cache=True)

def gpu_ctrl_adapt(ctrl_unit,func_list):
    return cuda.jit(ctrl_unit, device=False, cache=True)


def ext_func_adapt(func):
    cache_base = "./__ptxcache__"
    cache_path = cache_base+"/hrm_"+func.__name__+"_dev.ptx"
    if not exists(cache_base) :
        mkdir(cache_base)
    if( (not exists(cache_path) ) or ( getmtime(cache_path) < func_defn_time(func) ) ):
        ptx = device_ptx(func)
        cache_file = open(cache_path,mode='w')
        cache_file.write(ptx)
    else:
        print("ptx already exists")
    return cache_path


def ext_ctrl_adapt(ctrl_unit,func_list):
    return cuda.jit(ctrl_unit, link=func_list, device=False, cache=True)


def bind_strat( ctrl_adapt, ctrl, func_adapt, func_list ):
    adapted_func_list = [ func_adapt(f) for f in func_list ]
    return ctrl_adapt(ctrl(adapted_func_list),adapted_func_list)






float64 = np.float64
int64   = np.int64
uint64  = np.uint64
bool_   = np.bool_

particle = numba.from_dtype(np.dtype([('x',    float64), ('ux',    float64), ('w',     float64),
                     ('seed', int64  ), ('event', int64  ), ('alive', bool_  ) ]))


external = cuda.declare_device('external', 'int32(float32)')

direct   = cuda.declare_device('direct', 'int32(float32)')

def simple( x : numba.uint32, y : numba.uint32 ) -> numba.uint64 :
    external(1.0)
    return x+y



def complicated(p : particle) :
    p.x     += 1
    p.ux    += 1
    p.event = external(p.x)
    p.w     += 1
    p.event = direct(p.x)
    p.seed  += 1
    p.event = external(p.x)
    p.event += 1
    p.event = direct(p.x)
    p.alive  = not p.alive
    #p.something_else += 1


type_map = {
    particle : "Particle"
}

function_map = {
    external : "external_function",
    direct   : "prog.template async<DUMMY>",
}

print(particle)

exit(1)
async_even = cuda.declare_device('prog.template async<Even>', 'void(int32)')
async_odd  = cuda.declare_device('prog.template async<Odd>' , 'void(int32)')
dev_state  = cuda.declare_device('prog.template async<Odd>' , 'void(int32)')

def even(value: numba.int32):
    if value % 2 == 0:
        async_even(value/2)
    else :
        async_odd(value/2)

def odd(value: numba.int32):
    if value % 2 == 0:
        async_even(value/2)
    else :
        async_odd(value/2)

def initialize():
    pass

def finalize():
    pass

def make_work() -> numba.types.literal(True):
    return True


base_fns   = (initialize,finalize,make_work)
state_spec = (np.int64,np.int32,np.int16) 
async_fns  = [complicated]

print(harmonize("ProgramSpec",function_map,type_map,state_spec,base_fns,async_fns))
#harmonize("ProgramSpec",function_map,type_map,state_spec,base_fns,async_fns)




if False :

    print(ext_func_adapt(simple))


    simple_inner = cuda.declare_device('simple_kernel', 'void()')

    @cuda.jit(device=False, link=["harm.ptx","./__ptxcache__/hrm_simple_dev.ptx"],debug=True,opt=False)
    def do_simple():
        simple_inner()


    do_simple[1,32]()

    #print(harm_func_trampoline(simple))

    print(ext_func_adapt(complicated))
    #print(harm_func_trampoline(complicated))

    #print(particle)



    #print(simple.__annotations__)
    #print(device_ptx(simple))

