*** Settings ***
Library    BuiltIn

*** Variables ***
${nome}

*** Test Cases ***
Criar Paciente Fake
    Log    Criando paciente ${nome}
    Log    RESULT::paciente_id=12345
