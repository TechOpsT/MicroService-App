{{- define "task-service.name" -}}
{{- .Release.Name }}-task-service
{{- end }}

{{- define "task-service.labels" -}}
app.kubernetes.io/name: task-service
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: taskflow
{{- end }}

{{- define "task-service.selectorLabels" -}}
app.kubernetes.io/name: task-service
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
