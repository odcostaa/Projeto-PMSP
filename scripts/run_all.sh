set -e
cd /home/claude
E="2026_01_prova_aluno_soldado 2025_02_prova_soldado_pmes2502 2023_01_prova_soldado_pmes2203 2019_02_prova_soldado_dp2 2018_02_prova_soldado_dp2 2017_02_prova_soldado_dp2 sem_ano_prova_view_7 sem_ano_prova_view_8 sem_ano_prova_view_10 sem_ano_prova_view_14 sem_ano_prova_view_15 sem_ano_prova_view_20"
rm -rf work/figs work/qi
python3 -I scripts/figs.py provas_zip work/figs $E | tail -1
python3 -I scripts/build_stream.py provas_zip work/stream $E | tail -1
python3 -I scripts/build_dataset.py >/dev/null
for t in pmes1703:2017_02_prova_soldado_dp2:50 pmes1803:2018_02_prova_soldado_dp2:60 pmes1902:2019_02_prova_soldado_dp2:60 pmes2203:2023_01_prova_soldado_pmes2203:60 pmes2502:2025_02_prova_soldado_pmes2502:60 pmes2601:2026_01_prova_aluno_soldado:60 pmes2104:sem_ano_prova_view_7:60 pmes1903:sem_ano_prova_view_8:60 pmes1901:sem_ano_prova_view_10:60 pmes1602:sem_ano_prova_view_14:50 pmes1501:sem_ano_prova_view_15:50 pmes1201:sem_ano_prova_view_20:50; do IFS=: read e n q <<< "$t"; python3 -I scripts/qimgs.py provas_zip/$n.pdf $n work/qi/$e $q | tail -1; done
python3 -I scripts/build_final.py
python3 -I scripts/imgpost.py
