*** Settings ***
Library    SeleniumLibrary
Library    driver_helper.py

*** Variables ***
${URL}    about:blank

*** Test Cases ***
Abrir Navegador Visivel
    ${headless}=    Set Variable If    '${SHOW_UI}' == 'True'    False    True
    Run Keyword If    '${SHOW_UI}' == 'True'    Log    SHOW_UI=True -> abrindo Chrome visível
    Run Keyword If    '${SHOW_UI}' != 'True'    Log    SHOW_UI=False -> abrindo Chrome headless
    ${driver}=    Create Chrome Driver    ${headless}
    Register Driver    ${driver}
    Sleep    60
    [Teardown]    Close All Browsers
