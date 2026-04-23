{{/*
Expand the name of the chart.
*/}}
{{- define "postgres.name" -}}
{{- .Release.Name }}-postgres
{{- end }}

{{/*
Common labels applied to all resources.
*/}}
{{- define "postgres.labels" -}}
app.kubernetes.io/name: postgres
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: taskflow
{{- end }}

{{/*
Selector labels used by Deployments and Services to match pods.
*/}}
{{- define "postgres.selectorLabels" -}}
app.kubernetes.io/name: postgres
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
