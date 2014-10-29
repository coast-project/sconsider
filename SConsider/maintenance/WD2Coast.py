import re

lowerCaseNamespaces = (
    re.compile(
        r'((Coast::)?(\b(Memory|Storage|Utility|System|URLUtils|Threading|Oracle|Security|StreamUtils|ITOStorage|TypeTraits|IO)\b::))'),
    lambda mo: 'coast::' + str(mo.group(3)).lower())

replaceTestFramework = (
    re.compile(r'(\b(TestFramework)\b::)'),
    lambda mo: 'testframework::'
)

replaceSysLog = (
    re.compile(r'(\b(SysLog)\b::)'),
    lambda mo: 'SystemLog::'
)

replaceSysLogIncludes = (
    re.compile(r'include\s*.SysLog\.h.'),
    'include "SystemLog.h"'
)

changeToTracer = (
    re.compile(r'include\s*.Dbg\.h.'),
    'include "Tracer.h"'
)

prefixStreamWithStd = (
    re.compile(r'(([^:.*<>&]{2})\b([iof]{1,2}stream|streamsize)\b)'),
    lambda mo: str(mo.group(2)) + 'std::' + str(mo.group(3))
)

prefixStreamModifiersWithStd = (
    re.compile(
        r'(([^:.*]{2})\b(flush|endl|hex|cerr|cout|setw|setprecision|setiosflags|setfill)\b)'),
    lambda mo: str(mo.group(2)) + 'std::' + str(mo.group(3)))

adjustCloneFunctionDecl = (
    re.compile(
        r'(^[ \t]+//.*$\s)?^([ \t]+)((virtual\s+)?IFAObject\s*\*\s*Clone\()(\)\s*const)',
        re.M),
    lambda mo:
        str(mo.group(2)) +
        '/*! @copydoc IFAObject::Clone(Allocator *) */\n' +
        str(mo.group(2)) +
        str(mo.group(3)) +
        'Allocator *a' +
        str(mo.group(5))
    )

# potentially spans multiple lines
adjustCloneFunctionDef = (
    re.compile(r'^([ \t]*)(IFAObject\s*\*\s*(\w+::)?Clone\()(\)\s*const)', re.M),
    lambda mo:
        str(mo.group(1)) +
        str(mo.group(2)) +
        'Allocator *a' +
        str(mo.group(4))
)

adjustCloneAllocatorNew = (
    re.compile(r'(return\s+new\s+)(\w+)', re.M),
    lambda mo:
        str(mo.group(1)) +
        '(a) ' +
        str(mo.group(2))
)

changeToTestCaseType = (
    re.compile(r'(TString\s+)\bname\b(\s*\)\s*:\s*TestCaseType\()\bname\b', re.M),
    lambda mo:
        str(mo.group(1)) +
        'tname' +
        str(mo.group(2)) +
        'tname'
)

replaceMetathing1 = (
    re.compile(r'MetaThing\(\s*\)'),
    lambda mo:
        'Anything(Anything::ArrayMarker())'
)

replaceMetathing2 = (
    re.compile(r'MetaThing\(([^)]*\))'),
    lambda mo:
        'Anything(Anything::ArrayMarker(), ' +
        str(mo.group(1))
)

replaceMetathing3 = (
    re.compile(r'MetaThing(\s+\w+)\(([^)]*\))'),
    lambda mo:
        'Anything' +
        str(mo.group(1)) +
        ' = Anything(Anything::ArrayMarker(), ' +
        str(mo.group(2))
)

replaceMetathing4 = (
    re.compile(r'MetaThing([^(])'),
    lambda mo:
        'Anything' +
        str(mo.group(1))
)

# in cpp files only
replaceMetathing5 = (
    re.compile(r'MetaThing(\s+\w+);'),
    lambda mo:
        'Anything' +
        str(mo.group(1)) +
        ' = Anything(Anything::ArrayMarker());'
)

# putAnyMapperReplacements = (
#     re.compile(
#         r'(Do(Final)?PutAny(\w+)?\(\s*const\s*char([^,]+)?,\s*Anything)\s+(value)'),
#     lambda mo: str(mo.group(1)) + ' const &' + str(mo.group(5)))

removeConfigIncludes = (
    re.compile(r'^#include\s*.config_[^.]*\.h.*\s*$\s', re.M),
    ''
)

removeOnlyStdIostream = (
    re.compile(
        r'(^[ \t]*#if.*defined.*ONLY_STD_IOSTREAM.*$\s)'
        '(^[ \t]*[^#][^e][^n][^d][^i][^f].*$\s)'
        '([ \t]*#endif\s*$\s+)',
        re.M
    ),
    '')

adjustUniqueIdGen = (
    re.compile(r'UniqueIdGen::GetUniqueId'),
    'coast::security::generateUniqueId'
)

replaceDoCheckStores = (
    re.compile(r'\bDoCheckStores\b'),
    'CheckStores'
)

replaceDoCheckStoresInTestCode = (
    re.compile(r'^([ \t]+)Do(CheckStores\()', re.M),
    lambda mo:
        str(mo.group(1)) +
        'Anything anyFailureStrings;\n' +
        str(mo.group(1)) +
        str(mo.group(2)) +
        'anyFailureStrings, '
)

from ChangeImportLines import reAny, reShell, reCpp, reHeader, reSconsider


def extendReplaceFuncMap(extensionToReplaceFuncMap):
    extensionToReplaceFuncMap[reAny] = [
        replaceDoCheckStores,
    ]
    extensionToReplaceFuncMap[reShell].extend([
    ])
    extensionToReplaceFuncMap[reCpp].extend([
        lowerCaseNamespaces,
        replaceSysLog,
        replaceTestFramework,
        changeToTracer,
        prefixStreamWithStd,
        prefixStreamModifiersWithStd,
        replaceSysLogIncludes,
        adjustCloneFunctionDecl,
        adjustCloneFunctionDef,
        adjustCloneAllocatorNew,
        changeToTestCaseType,
        replaceMetathing1,
        replaceMetathing2,
        replaceMetathing3,
        replaceMetathing4,
        replaceMetathing5,
#         putAnyMapperReplacements,
        removeConfigIncludes,
        removeOnlyStdIostream,
        adjustUniqueIdGen,
        replaceDoCheckStores,
        replaceDoCheckStoresInTestCode,
    ])
    extensionToReplaceFuncMap[reHeader].extend([
        lowerCaseNamespaces,
        replaceSysLog,
        replaceTestFramework,
        changeToTracer,
        prefixStreamWithStd,
        prefixStreamModifiersWithStd,
        replaceSysLogIncludes,
        adjustCloneFunctionDecl,
        adjustCloneFunctionDef,
        adjustCloneAllocatorNew,
        changeToTestCaseType,
        replaceMetathing1,
        replaceMetathing2,
        replaceMetathing3,
        replaceMetathing4,
#         putAnyMapperReplacements,
        removeConfigIncludes,
        removeOnlyStdIostream,
        adjustUniqueIdGen,
    ])
    extensionToReplaceFuncMap[reSconsider].extend([
    ])
