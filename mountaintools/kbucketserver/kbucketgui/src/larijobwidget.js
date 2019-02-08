exports.LariJobWidget = LariJobWidget;

let KBClient=require('kbclient').v1;

function LariJobWidget() {
  this.element = function() {
    return m_element;
  };
  this.setLariId = function(id) {
    setLariId(id);
  };
  this.setLariJobId = function(id) {
    setLariJobId(id);
  };

  let m_lari_id = '';
  let m_lari_job_id = '';

  var m_element = $(`
		<span>
			<div class="ml-vlayout">
        <div class="ml-vlayout-item" style="flex:150px 0 0;max-width:500px">
          <table class=table>
            <tr>
              <th>LARI ID</th>
              <td><span id=lari_id></span></td>
            </tr>
            <tr>
              <th>LARI JOB ID</th>
              <td><span id=lari_job_id></span></td>
            </tr>
            <tr>
              <th>Status</th>
              <td><span id=status></span></td>
            </tr>
          </table>
        </div>
				<div class="ml-vlayout-item" style="flex:1">
					<div class="ml-item-content" id="left_panel" style="margin:10px; background:">
            <span id=console_out></span>
					</div>
				</div
			</div>
		</span>
	`);

  function setLariId(id) {
    if (m_lari_id==id) return;
    m_lari_id=id;
    refresh();
  }

  function setLariJobId(id) {
    if (m_lari_job_id==id) return;
    m_lari_job_id=id;
    refresh();
  }

  function get_status_from_obj(obj) {
    if (!obj.is_complete) {
      return 'incomplete';
    }
    if (!obj.result) {
      return 'problem';
    }
    if (obj.result.success) {
      return 'finished';
    }
    return 'error';
  }

  function refresh() {
    m_element.find('#lari_id').html(m_lari_id);
    m_element.find('#lari_job_id').html(m_lari_job_id);
    m_element.find('#console_out').html('');
    if ((!m_lari_id)||(!m_lari_job_id))
      return;
    m_element.find('#console_out').html('Loading...');
    let KBC=new KBClient();
    KBC.readTextFile(`kbucket://${m_lari_id}/jobs/${m_lari_job_id}.json`)
      .then(function(txt) {
        let obj;
        try {
          obj=JSON.parse(txt);
        }
        catch(err) {
          console.error(txt);
          m_element.find('#status').html('Error parsing JSON.');
          return;
        }
        let status=get_status_from_obj(obj);
        m_element.find('#status').html(status);
      })
      .catch(function(err) {
        console.error(err);
        m_element.find('#status').html('Loading error: '+err.message);
      });
    KBC.readTextFile(`kbucket://${m_lari_id}/jobs/${m_lari_job_id}.console.out`)
      .then(function(txt) {
        window.test_text=txt;
        m_element.find('#console_out').html('<pre>'+txt+'</pre>');
      })
      .catch(function(err) {
        console.error(err);
        m_element.find('#console_out').html('Loading error: '+err.message);
      });
  }
}