As admin user

create user app_data identified by H0tsummer2025
default tablespace data;

grant connect, resource to app_data;
alter user app_data quota unlimited on data;

drop user ras_admin cascade;
create user ras_admin identified by H0tsummer#2025
default tablespace data;
grant connect, resource to ras_admin;
alter user ras_admin quota unlimited on data;

create role nl2sql_role;
grant select on app_data.vendors to nl2sql_role;
grant select on app_data.ACCOUNT_PAYABLES_TBL to nl2sql_role;
grant select on app_data.INVOICE_TYPE_LOOKUP to nl2sql_role;
grant nl2sql_role to ras_admin with admin option;

grant create session, xs_session_admin to ras_admin;
EXEC XS_ADMIN_CLOUD_UTIL.GRANT_SYSTEM_PRIVILEGE('PROVISION','ras_admin');
EXEC XS_ADMIN_CLOUD_UTIL.GRANT_SYSTEM_PRIVILEGE('ADMIN_ANY_SEC_POLICY','ras_admin');
--------------------

BEGIN sys.xs_principal.revoke_roles('blake'); END;
/
BEGIN sys.xs_principal.delete_principal('blake'); END;
/
BEGIN
  SYS.XS_ACL.DELETE_ACL('superuser_app_acl');
END;
/
BEGIN
  SYS.XS_ACL.DELETE_ACL('inv_type_limited_acl');
END;
/
BEGIN
  SYS.XS_ACL.DELETE_ACL('inv_type_redact_acl');
END;
/
BEGIN sys.xs_principal.delete_principal('superuser_app_role'); END;
/
BEGIN sys.xs_principal.delete_principal('inv_type_limited_role'); END;
/
BEGIN sys.xs_principal.delete_principal('inv_type_redact_role'); END;
/
----
exec sys.xs_principal.create_role(name => 'superuser_app_role', enabled => true);
exec sys.xs_principal.create_role(name => 'inv_type_limited_role', enabled => true);
exec sys.xs_principal.create_role(name => 'inv_type_redact_role', enabled => true);


grant nl2sql_role to superuser_app_role;
grant nl2sql_role to inv_type_limited_role;
grant nl2sql_role to inv_type_redact_role;

SELECT STANDARD_HASH('test', 'SHA256') FROM dual;

exec  sys.xs_principal.create_user(name => 'rajarora', schema => 'app_data');
exec  sys.xs_principal.set_password('rajarora', 'G0ingtothest#rs');
exec  sys.xs_principal.grant_roles('rajarora', 'XSCONNECT');
exec  sys.xs_principal.grant_roles('rajarora', 'superuser_app_role');

exec  sys.xs_principal.create_user(name => 'rajarora1', schema => 'app_data');
exec  sys.xs_principal.set_password('rajarora1', 'G0ingtothest#rs');
exec  sys.xs_principal.grant_roles('rajarora1', 'XSCONNECT');
exec  sys.xs_principal.grant_roles('rajarora1', 'inv_type_redact_role');

exec  sys.xs_principal.create_user(name => 'rajarora2', schema => 'app_data');
exec  sys.xs_principal.set_password('rajarora2', 'G0ingtothest#rs');
exec  sys.xs_principal.grant_roles('rajarora2', 'XSCONNECT');
exec  sys.xs_principal.grant_roles('rajarora2', 'inv_type_limited_role');



CREATE OR REPLACE PACKAGE app_data.ns_handlers AS
  FUNCTION dummy_handler(
    template_name IN VARCHAR2,
    attribute_name IN VARCHAR2,
    old_value IN VARCHAR2,
    new_value IN VARCHAR2
  ) RETURN VARCHAR2;
END ns_handlers;
/

CREATE OR REPLACE PACKAGE BODY app_data.ns_handlers AS
  FUNCTION dummy_handler(
    template_name IN VARCHAR2,
    attribute_name IN VARCHAR2,
    old_value IN VARCHAR2,
    new_value IN VARCHAR2
  ) RETURN VARCHAR2 IS
  BEGIN
    RETURN new_value;
  END dummy_handler;
END ns_handlers;
/

DECLARE
  attrs XS$NS_ATTRIBUTE_LIST;
BEGIN
  attrs := XS$NS_ATTRIBUTE_LIST();
  attrs.extend(1);
  attrs(1) := XS$NS_ATTRIBUTE('attr1','value1');
  SYS.XS_NAMESPACE.CREATE_TEMPLATE('ns1', attrs, 'app_data',
                                   'NS_HANDLERS','dummy_handler',
                                   'SYS.NS_UNRESTRICTED_ACL',
                                   'NL2SQLAttributes');
END;
/

DECLARE
  sessionid RAW(16);
  attrib_out_val VARCHAR2(4000);
BEGIN
  SYS.DBMS_XS_SESSIONS.CREATE_SESSION('rajarora', sessionid);
  SYS.DBMS_XS_SESSIONS.ATTACH_SESSION(sessionid);
  SYS.DBMS_XS_SESSIONS.CREATE_NAMESPACE('ns1');
  SYS.DBMS_XS_SESSIONS.SET_ATTRIBUTE('ns1', 'attr1', 'val13');
  SYS.DBMS_XS_SESSIONS.GET_ATTRIBUTE('ns1', 'attr1', attrib_out_val);
  dbms_output.put_line(attrib_out_val);
  SYS.DBMS_XS_SESSIONS.DETACH_SESSION;
  SYS.DBMS_XS_SESSIONS.DESTROY_SESSION(sessionid);
END;
/


CREATE OR REPLACE FUNCTION get_xs_attribute(
    p_namespace VARCHAR2,
    p_attribute VARCHAR2
) RETURN VARCHAR2 IS
    v_value VARCHAR2(4000);
BEGIN
    SYS.DBMS_XS_SESSIONS.GET_ATTRIBUTE(
        p_namespace,
        p_attribute,
        v_value
    );
    RETURN v_value;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
/

grant execute on get_xs_attribute to nl2sql_role;

-- exec  sys.xs_principal.grant_roles('rajarora, 'XSNAMESPACEADMIN');

declare
begin
  sys.xs_security_class.create_security_class(
    name        => 'app_privs',
    parent_list => xs$name_list('sys.dml'),
    priv_list   => xs$privilege_list(xs$privilege('invoice_privs')));
end;
/

BEGIN
  SYS.XS_SECURITY_CLASS.DELETE_SECURITY_CLASS('app_privs',XS_ADMIN_UTIL.DEFAULT_OPTION);
END;

-- exec sys.xs_principal.create_role(name => 'superuser_app_role', enabled => true);
-- exec sys.xs_principal.create_role(name => 'inv_type_limited_role', enabled => true);
-- exec sys.xs_principal.create_role(name => 'inv_type_redact_role', enabled => true);


declare
  aces xs$ace_list := xs$ace_list();
begin
  aces.extend(1);

  aces(1) := xs$ace_type(privilege_list => xs$name_list('select','invoice_privs'),
                         principal_name => 'superuser_app_role');

  sys.xs_acl.create_acl(name      => 'superuser_app_acl',
                    ace_list  => aces,
                    sec_class => 'app_privs');

  aces(1) := xs$ace_type(privilege_list => xs$name_list('select'),
                         principal_name => 'inv_type_redact_role');

  sys.xs_acl.create_acl(name      => 'inv_type_redact_acl',
                    ace_list  => aces,
                    sec_class => 'app_privs');

aces(1) := xs$ace_type(privilege_list => xs$name_list('select','invoice_privs'),
                                           principal_name => 'inv_type_limited_role');

  sys.xs_acl.create_acl(name      => 'inv_type_limited_acl',
                    ace_list  => aces,
                    sec_class => 'app_privs');
end;
/


declare
  realms   xs$realm_constraint_list := xs$realm_constraint_list();
  cols     xs$column_constraint_list := xs$column_constraint_list();
begin
  realms.extend(3);

  realms(1) := xs$realm_constraint_type(
    -- realm    => 'vendor_site_details = ''BRISTOL Bristol''',
    realm    => '1 = 1',
    acl_list => xs$name_list('superuser_app_acl'));

  realms(2) := xs$realm_constraint_type(
    realm  => '1 = 1',
    acl_list => xs$name_list('inv_type_redact_acl'));

  realms(3) := xs$realm_constraint_type(
    realm  => 'invoice_type = get_xs_attribute(''ns1'',''attr1'')',   -- use get_xs_attribute realm  => 'invoice_type = xs_sys_context(''ns1'',''attr1'')'
    acl_list => xs$name_list('inv_type_limited_acl'));

  cols.extend(1);
  cols(1) := xs$column_constraint_type(
    column_list => xs$list('invoice_type'),
    privilege   => 'invoice_privs');

  sys.xs_data_security.create_policy(
    name                   => 'invoice_type_ds',
    realm_constraint_list  => realms,
    column_constraint_list => cols);
end;
/

begin
  sys.xs_data_security.apply_object_policy(
    policy => 'invoice_type_ds',
    schema => 'app_data',
    object =>'invoice_type_lookup');
end;
/

begin
  sys.xs_data_security.remove_object_policy(
  policy => 'invoice_type_ds',
  schema => 'app_data',
  object =>'invoice_type_lookup');
end;
/

BEGIN
 SYS.XS_DATA_SECURITY.DELETE_POLICY(
 policy => 'invoice_type_ds',
 delete_option =>XS_ADMIN_UTIL.DEFAULT_OPTION   -- For CASCADE
);
END;
/

SELECT p.object_owner,
       f.object_type,
       p.policy_group,
       p.object_name,
       p.policy_name,
       p.enable,
       p.pf_owner,
       f.status as function_status
FROM dba_policies p
LEFT JOIN dba_objects f
  ON f.owner = p.pf_owner
  AND f.object_type = 'FUNCTION'
ORDER BY p.object_owner, p.object_name;

begin
  if (sys.xs_diag.validate_workspace()) then
    dbms_output.put_line('All configurations are correct.');
  else
    dbms_output.put_line('Some configurations are incorrect.');
  end if;
end;
/
-- XS$VALIDATION_TABLE contains validation errors if any.
-- Expect no rows selected.
select * from xs$validation_table order by 1, 2, 3, 4;

BEGIN sys.xs_principal.revoke_roles('blake'); END;
