{{/*
Expand the name of the chart.
*/}}
{{- define "ahoy.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "ahoy.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create ahoy server name and version as used by the chart label.
*/}}
{{- define "ahoy.server.fullname" -}}
{{- printf "%s-%s" (include "ahoy.fullname" .) "server" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ahoy.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ahoy.labels" -}}
helm.sh/chart: {{ include "ahoy.chart" . }}
{{ include "ahoy.selectorLabels" . }}
app.kubernetes.io/version: {{ .Values.image.tag | default .Chart.AppVersion | trunc 63 | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ahoy.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ahoy.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ahoy.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ahoy.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create a default fully qualified app name for the postgres requirement.
*/}}
{{- define "ahoy.postgresql.fullname" -}}
{{- $postgresContext := dict "Values" .Values.postgresql "Release" .Release "Chart" (dict "Name" "postgresql") -}}
{{ include "postgresql.primary.fullname" $postgresContext }}
{{- end }}
