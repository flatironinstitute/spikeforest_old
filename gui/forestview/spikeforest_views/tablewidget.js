window.TableWidget = TableWidget;

function TableWidget(elmt) {
    let that=this;
    this.onSelectionChanged=function(handler) {
        m_selection_changed_handlers.push(handler);
    }
    this.setCurrentRowIndex=function(index) {
        elmt.find('.tablewidget_row').removeClass('current');
        elmt.find('.tablewidget_row').removeClass('selected');
        if (index !== null) {
            elmt.find('.tablewidget_row#'+index).addClass('current');
            elmt.find('.tablewidget_row#'+index).addClass('selected');
        }
    }

    let m_selection_changed_handlers=[];

    let rows = elmt.find('.tablewidget_row');
    rows.each(function(index) {
        let row = $(this);
        row.click(function() {
            elmt.find('.tablewidget_row').removeClass('current');
            elmt.find('.tablewidget_row').removeClass('selected');
            row.addClass('current');
            row.addClass('selected');
            _call_selection_changed_handlers();
        });
    });

    function _call_selection_changed_handlers() {
        let current_id = elmt.find('.tablewidget_row.current').attr('id');
        let selected_ids = [];
        elmt.find('.tablewidget_row.selected').each(function() {
            selected_ids.push($(this).attr('id'));
        });
        m_selection_changed_handlers.forEach(function(handler) {
            handler(current_id, selected_ids);
        });
    }
}