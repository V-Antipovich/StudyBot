// Функция поиска данных по ключевому слову в табличке
function tableSearch(){
    var phrase = document.getElementById('search-text');
    var table = document.getElementById('sortable_searchable');
    var regPhrase = new RegExp(phrase.value, 'i');
    var flag = false;
    for (var i = 1; i < table.rows.length; i++) {
        flag = false;
        for (var  j = table.rows[i].cells.length - 1; j >= 0; j--) {
            flag = regPhrase.test(table.rows[i].cells[j].innerHTML);
            if (flag) break;
        }
        if (flag) {
            table.rows[i].style.display = "";
        }
        else {
            table.rows[i].style.display = 'none';
        }
    }
}