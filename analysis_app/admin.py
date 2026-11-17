from django.contrib import admin
from .models import Politician, Speech, TranscriptSegment, Ngram, IssueMention, ProcessingLog

admin.site.register(Politician)
admin.site.register(Speech)
admin.site.register(TranscriptSegment)
admin.site.register(Ngram)
admin.site.register(IssueMention)
admin.site.register(ProcessingLog)
