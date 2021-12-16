# Problem Scheduler

Introduzir horário e salas disponíveis na pasta **data**. Atribuir os seguintes nomes de acordo com o ficheiro (Exemplo):

    ADS - Exemplo de horario do 1o Semestre.csv --> timetable.csv
    ADS - Caracterizacao das salas.csv --> rooms.csv

Para correr este projeto, ou seja, iniciar a resolução do calendário é necessário correr o seguinte script que se encontra na pasta **scripts**:

    ./initialize.sh

Depois de verificar que o container acabou de correr, correr o seguinte script (pasta **scripts**) para copiar o calendário/horário gerado:

    ./copy_results.sh

