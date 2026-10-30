"""Spring Security authentication contracts.

Not a RuoYi file
----------------
``com.ruoyi`` contains no authentication provider of its own: ``SysLoginService`` calls the
Spring Security ``AuthenticationManager`` bean, which is wired by ``SecurityConfig``::

    auth.userDetailsService(userDetailsService).passwordEncoder(bCryptPasswordEncoder());

This package mirrors the three Spring types involved, in the same shape a Java developer
expects:

============================  ====================================================
Spring                        Python
============================  ====================================================
``AuthenticationManager``     :mod:`app.framework.security.authentication.authentication_manager`
``ProviderManager``           :mod:`app.framework.security.authentication.provider_manager`
``DaoAuthenticationProvider`` :mod:`app.framework.security.authentication.dao_authentication_provider`
============================  ====================================================
"""
