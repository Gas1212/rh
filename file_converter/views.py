# file_converter/views.py
import io
import tempfile
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def convert_to_pdf(request):
    """
    Vue simple pour convertir un fichier en PDF avec Aspose.PDF
    """
    if request.method == 'POST' and 'file' in request.FILES:
        file = request.FILES['file']
        filename = file.name.rsplit('.', 1)[0]

        try:
            # Enregistrer le fichier temporairement
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(file.read())
                input_path = tmp.name

            # Conversion avec Aspose
            pdf = AsposePdf(input_path)  # ⚠️ Remplace par ta logique réelle Aspose
            buffer = io.BytesIO()
            pdf.save(buffer)

            # Réponse HTTP avec le PDF
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return response

        except Exception as e:
            return HttpResponse(f"Erreur : {e}", status=500)

    # Si GET : afficher le formulaire d’upload
    return render(request, 'file_converter/converter.html')
