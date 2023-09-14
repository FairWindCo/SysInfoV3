import ntsecuritycon
import win32security

from fw_automations_utils.win_file_permissions import print_obj_info, get_mode

FILENAME = "d:\\3"


def access_type(aceType):
    if aceType == 0:
        return 'ACCESS RIGHT:'
    elif aceType == 1:
        return 'DENY RIGHT:'
    else:
        return "UNKNOWN:"


def access_mask(aceMask):
    flags = []
    if aceMask & ntsecuritycon.GENERIC_ALL:
        flags.append('GENERIC_ALL')
    if aceMask & ntsecuritycon.GENERIC_EXECUTE:
        flags.append('GENERIC_EXECUTE')
    if aceMask & ntsecuritycon.GENERIC_WRITE:
        flags.append('GENERIC_WRITE')
    if aceMask & ntsecuritycon.GENERIC_READ:
        flags.append('GENERIC_READ')
    if aceMask & ntsecuritycon.DELETE:
        flags.append('DELETE')
    if aceMask & ntsecuritycon.READ_CONTROL:
        flags.append('READ_CONTROL')
    if aceMask & ntsecuritycon.WRITE_DAC:
        flags.append('WRITE_DAC')
    if aceMask & ntsecuritycon.WRITE_OWNER:
        flags.append('WRITE_OWNER')
    if aceMask & ntsecuritycon.SYNCHRONIZE:
        flags.append('SYNCHRONIZE')
    if aceMask & ntsecuritycon.MAXIMUM_ALLOWED:
        flags.append('MAXIMUM_ALLOWED')
    if aceMask & ntsecuritycon.ACCESS_SYSTEM_SECURITY:
        flags.append('ACCESS_SYSTEM_SECURITY')
    if aceMask & ntsecuritycon.STANDARD_RIGHTS_REQUIRED:
        flags.append('STANDARD_RIGHTS_REQUIRED')

    if aceMask & ntsecuritycon.FILE_READ_DATA:
        flags.append('FILE_READ_DATA|FILE_LIST_DIRECTORY')
    if aceMask & ntsecuritycon.FILE_WRITE_DATA:
        flags.append('FILE_WRITE_DATA|FILE_ADD_FILE')
    if aceMask & ntsecuritycon.FILE_APPEND_DATA:
        flags.append('FILE_APPEND_DATA|FILE_ADD_SUBDIRECTORY|FILE_CREATE_PIPE_INSTANCE')
    if aceMask & ntsecuritycon.FILE_READ_EA:
        flags.append('FILE_READ_EA')
    if aceMask & ntsecuritycon.FILE_WRITE_EA:
        flags.append('FILE_WRITE_EA')
    if aceMask & ntsecuritycon.FILE_EXECUTE:
        flags.append('FILE_EXECUTE|FILE_TRAVERSE')
    if aceMask & ntsecuritycon.FILE_DELETE_CHILD:
        flags.append('FILE_DELETE_CHILD')
    if aceMask & ntsecuritycon.FILE_READ_ATTRIBUTES:
        flags.append('FILE_READ_ATTRIBUTES')
    if aceMask & ntsecuritycon.FILE_WRITE_ATTRIBUTES:
        flags.append('FILE_WRITE_ATTRIBUTES')
    return flags


def ace_flags(aceFlags):
    flags = []
    if aceFlags & win32security.CONTAINER_INHERIT_ACE:
        flags.append(('CONTAINER_INHERIT_ACE', 'The ACE is inherited by the container objects.'))
    if aceFlags & win32security.NO_PROPAGATE_INHERIT_ACE:
        flags.append(('NO_PROPAGATE_INHERIT_ACE', 'The OBJECT_INHERIT_ACE and CONTAINER_INHERIT_ACE '
                                                  'bits are not propagated to an inherited ACE.'))
    if aceFlags & win32security.OBJECT_INHERIT_ACE:
        flags.append(('OBJECT_INHERIT_ACE', 'The ACE is inherited by non-container objects.'))
    if aceFlags & win32security.INHERITED_ACE:
        flags.append(('INHERITED_ACE',
                      'Indicates an inherited ACE. '
                      'This flag allows operations that change the security on a tree of objects to modify inherited '
                      'ACEs while not changing ACEs that were directly applied to the object.'))
    if aceFlags & win32security.INHERIT_ONLY_ACE:
        flags.append(('INHERIT_ONLY_ACE',
                      'The ACE does not apply to the object the ACE is assigned to, but it can be inherited by child objects.'))
    return flags


def print_ace_flags(aceFlags):
    flags_names = ace_flags((aceFlags))
    return f'[{",".join(map(lambda a: a[0], flags_names))}]'


def print_mask_flags(aceMask):
    flags_names = access_mask((aceMask))
    return f'[{",".join(flags_names)}]'


def print_acl(acl_desc):
    len_ac = acl_desc.GetAceCount()
    for index in range(len_ac):
        ((aceType, aceFlags), mask, sid, *other) = acl_desc.GetAce(index)
        name, autority, code = win32security.LookupAccountSid(None, sid)
        print(access_type(aceType), print_ace_flags(aceFlags), print_mask_flags(mask), name, autority, code, other)


sd = win32security.GetFileSecurity(FILENAME, win32security.DACL_SECURITY_INFORMATION |
                                   win32security.OWNER_SECURITY_INFORMATION |
                                   win32security.GROUP_SECURITY_INFORMATION
                                   )
dacl = sd.GetSecurityDescriptorDacl()  # instead of dacl = win32security.ACL()
print_acl(dacl)

sd.SetSecurityDescriptorDacl(1, dacl, 0)  # may not be necessary
# win32security.SetFileSecurity(FILENAME, win32security.DACL_SECURITY_INFORMATION, sd)

print_obj_info(FILENAME)
