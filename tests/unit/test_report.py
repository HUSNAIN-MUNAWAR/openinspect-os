from services.reporting.pdf import generate_mission_report

def test_pdf_report_generation(tmp_path):
    out = tmp_path/'report.pdf'
    generate_mission_report({'mission':'M1','facility':'F1','asset':'A1','coverage_percent':75,'findings':[{'type':'candidate','severity':'review-required','notes':'test','measurement':{'visibility':0.4}}]}, out)
    assert out.exists()
    assert out.read_bytes().startswith(b'%PDF')
