#!/usr/bin/env bash
# Download an issue (description, notes/comments, attachment links) from
# Redmine, GitHub or GitLab as a Markdown file. Read-only: GET requests and
# `gh issue view` only.
#
# Usage: download_issue.sh [--force] <issue-number> [output-file]
#
# Run it from the project root. Default output: issues/issue-<n>.md.
# If the output file exists with different content, exit code 3 and the
# file is left as it is, unless --force.
#
# Configuration: environment variables, or KEY=value lines in
# .claude/.env.claude of the project (environment variables win):
#   ISSUE_TRACKER    redmine | github | gitlab
#   REDMINE_URL      e.g. https://redmine.example.com
#   REDMINE_API_KEY  API key of the Redmine user
#   GITLAB_URL       e.g. https://gitlab.example.com
#   GITLAB_TOKEN     personal access token with scope read_api
#   GITLAB_PROJECT   optional: group/project or numeric id (default: from
#                    the origin remote)
# GitHub uses `gh`, authenticated with `gh auth login`.
#
# Tokens are never printed and are not passed on the curl command line.

set -euo pipefail

die() {
    printf 'ERRORE: %s\n' "$1" >&2
    exit "${2:-1}"
}

force=0
if [[ "${1:-}" == "--force" ]]; then
    force=1
    shift
fi

iid="${1:-}"
iid="${iid#\#}"
[[ "$iid" =~ ^[1-9][0-9]*$ ]] \
    || die "uso: download_issue.sh [--force] <numero-issue> [file]"

project_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
config_file="${ISSUE_CONFIG_FILE:-$project_root/.claude/.env.claude}"
output="${2:-$project_root/issues/issue-$iid.md}"

# Read the known keys from the config file without sourcing it.
load_config() {
    local key value
    [[ -f "$config_file" ]] || return 0
    while IFS='=' read -r key value || [[ -n "$key" ]]; do
        key="${key//[[:space:]]/}"
        case "$key" in
            ISSUE_TRACKER|REDMINE_URL|REDMINE_API_KEY|GITLAB_URL|GITLAB_TOKEN|GITLAB_PROJECT) ;;
            *) continue ;;
        esac
        [[ -n "${!key:-}" ]] && continue
        value="${value%$'\r'}"
        value="${value#"${value%%[![:space:]]*}"}"
        value="${value%"${value##*[![:space:]]}"}"
        value="${value#\"}"; value="${value%\"}"
        value="${value#\'}"; value="${value%\'}"
        export "$key=$value"
    done < "$config_file"
}

load_config

tracker="${ISSUE_TRACKER:-}"
[[ -n "$tracker" ]] || die "ISSUE_TRACKER non impostato (redmine, github o gitlab)"

command -v jq >/dev/null || die "jq non installato"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

today="$(date +%F)"

# GET <url> into <file> with the header in $auth_header.
http_get() {
    local url="$1" file="$2" status msg
    status="$(curl -sS -o "$file" -w '%{http_code}' \
        --connect-timeout 15 --max-time 60 \
        -H @<(printf '%s\n' "$auth_header") \
        "$url")" \
        || die "connessione a ${url%%/api/*} fallita (VPN attiva?)"
    if [[ "$status" != 2* ]]; then
        msg="$(jq -r '.message // .error // (.errors // empty | tostring) // empty' \
            "$file" 2>/dev/null | head -c 300 || true)"
        case "$status" in
            401) die "credenziali non valide o scadute (HTTP 401)" ;;
            403) die "credenziali senza permessi sulla issue (HTTP 403)" ;;
            404) die "issue #$iid non trovata (HTTP 404)" ;;
            *) die "il gestionale ha risposto HTTP $status ${msg}" ;;
        esac
    fi
}

# group/project from the origin remote (ssh, scp-like or https).
gitlab_project_from_remote() {
    local url
    url="$(git remote get-url origin 2>/dev/null)" \
        || die "GITLAB_PROJECT non impostato e remote origin assente"
    url="${url%.git}"
    case "$url" in
        *://*) url="${url#*://}"; url="${url#*/}" ;;
        *:*) url="${url#*:}" ;;
        *) die "remote origin non riconosciuto: imposta GITLAB_PROJECT" ;;
    esac
    printf '%s' "${url#/}"
}

case "$tracker" in
    redmine)
        [[ -n "${REDMINE_URL:-}" ]] || die "REDMINE_URL non impostato"
        [[ -n "${REDMINE_API_KEY:-}" ]] || die "REDMINE_API_KEY non impostato"
        command -v curl >/dev/null || die "curl non installato"
        base="${REDMINE_URL%/}"
        auth_header="X-Redmine-API-Key: $REDMINE_API_KEY"
        http_get "$base/issues/$iid.json?include=journals,attachments" \
            "$tmp_dir/issue.json"
        jq -r --arg web "$base/issues/$iid" --arg today "$today" '
            def day: if . then .[0:16] | sub("T"; " ") | sub("Z$"; "")
                else "-" end;
            .issue
            | "# #\(.id) \(.subject)\n",
            "- **Fonte:** redmine - \($web)",
            "- **Tipo:** \(.tracker.name // "-")",
            "- **Stato:** \(.status.name // "-")",
            "- **Priorità:** \(.priority.name // "-")",
            "- **Versione:** \(.fixed_version.name // "-")",
            "- **Autore:** \(.author.name // "-")",
            "- **Assegnatario:** \(.assigned_to.name // "-")",
            "- **Scaricata il:** \($today)",
            "",
            "## Descrizione\n",
            (.description // "" | if . == "" then "_Nessuna descrizione._"
                else . end),
            "",
            (.attachments // []) as $att
            | (if ($att | length) == 0 then empty else
                "## Allegati\n",
                ($att[] | "- \(.filename) - \(.content_url)"),
                ""
              end),
            ((.journals // []) | map(select((.notes // "") != ""))) as $notes
            | if ($notes | length) == 0 then empty else
                "## Note\n",
                ($notes[] |
                    "### \(.user.name // "-") - \(.created_on | day)\n",
                    .notes,
                    "")
              end
        ' "$tmp_dir/issue.json" > "$tmp_dir/out.md"
        ;;

    github)
        command -v gh >/dev/null || die "gh non installato"
        gh auth status >/dev/null 2>&1 \
            || die "gh non autenticato: esegui gh auth login"
        gh issue view "$iid" \
            --json number,title,body,state,url,labels,milestone,author,assignees,comments \
            > "$tmp_dir/issue.json" 2> "$tmp_dir/err.txt" \
            || die "gh issue view fallito: $(head -c 300 "$tmp_dir/err.txt")"
        jq -r --arg today "$today" '
            def day: if . then .[0:16] | sub("T"; " ") else "-" end;
            def names: if length > 0 then map(.login) | join(", ")
                else "-" end;
            "# #\(.number) \(.title)\n",
            "- **Fonte:** github - \(.url)",
            "- **Tipo:** \(if (.labels | length) > 0
                then .labels | map(.name) | join(", ") else "-" end)",
            "- **Stato:** \(.state)",
            "- **Versione:** \(.milestone.title // "-")",
            "- **Autore:** \(.author.login // "-")",
            "- **Assegnatario:** \(.assignees // [] | names)",
            "- **Scaricata il:** \($today)",
            "",
            "## Descrizione\n",
            (.body // "" | if . == "" then "_Nessuna descrizione._"
                else . end),
            "",
            ((.comments // []) | map(select((.body // "") != ""))) as $c
            | if ($c | length) == 0 then empty else
                "## Note\n",
                ($c[] |
                    "### \(.author.login // "-") - \(.createdAt | day)\n",
                    .body,
                    "")
              end
        ' "$tmp_dir/issue.json" > "$tmp_dir/out.md"
        ;;

    gitlab)
        [[ -n "${GITLAB_URL:-}" ]] || die "GITLAB_URL non impostato"
        [[ -n "${GITLAB_TOKEN:-}" ]] || die "GITLAB_TOKEN non impostato"
        command -v curl >/dev/null || die "curl non installato"
        project="${GITLAB_PROJECT:-$(gitlab_project_from_remote)}"
        api="${GITLAB_URL%/}/api/v4/projects/$(jq -rn --arg p "$project" '$p|@uri')"
        auth_header="PRIVATE-TOKEN: $GITLAB_TOKEN"
        http_get "$api/issues/$iid" "$tmp_dir/issue.json"

        # Notes, all pages, oldest first. System notes are dropped below.
        echo '[]' > "$tmp_dir/notes.json"
        page=1
        while :; do
            http_get "$api/issues/$iid/notes?sort=asc&order_by=created_at&per_page=100&page=$page" \
                "$tmp_dir/page.json"
            [[ "$(jq 'length' "$tmp_dir/page.json")" -gt 0 ]] || break
            jq -s '.[0] + .[1]' "$tmp_dir/notes.json" "$tmp_dir/page.json" \
                > "$tmp_dir/merged.json"
            mv "$tmp_dir/merged.json" "$tmp_dir/notes.json"
            page=$((page + 1))
        done

        jq -r --slurpfile notes "$tmp_dir/notes.json" --arg today "$today" '
            # Relative upload links (/uploads/...) point to the project.
            (.web_url | sub("/-/issues/[0-9]+$"; "")) as $project_url
            | def fix_links: gsub("\\]\\(/uploads/";
                "](\($project_url)/uploads/");
            def day: if . then .[0:16] | sub("T"; " ") else "-" end;
            def names: if length > 0 then map(.username) | join(", ")
                else "-" end;
            "# #\(.iid) \(.title)\n",
            "- **Fonte:** gitlab - \(.web_url)",
            "- **Tipo:** \(if (.labels | length) > 0
                then .labels | join(", ") else "-" end)",
            "- **Stato:** \(.state)",
            "- **Versione:** \(.milestone.title // "-")",
            "- **Autore:** \(.author.username // "-")",
            "- **Assegnatario:** \(.assignees // [] | names)",
            "- **Scadenza:** \(.due_date // "-")",
            "- **Scaricata il:** \($today)",
            "",
            "## Descrizione\n",
            ((.description // "" | fix_links)
                | if . == "" then "_Nessuna descrizione._" else . end),
            "",
            ($notes[0] | map(select((.system | not)
                and ((.body // "") != "")))) as $c
            | if ($c | length) == 0 then empty else
                "## Note\n",
                ($c[] |
                    "### \(.author.username) - \(.created_at | day)\n",
                    (.body | fix_links),
                    "")
              end
        ' "$tmp_dir/issue.json" > "$tmp_dir/out.md"
        ;;

    *)
        die "ISSUE_TRACKER non valido: $tracker (redmine, github o gitlab)"
        ;;
esac

# Same content apart from the download date: nothing to do.
if [[ -f "$output" ]]; then
    if diff -q <(grep -v '^- \*\*Scaricata il:\*\*' "$output") \
               <(grep -v '^- \*\*Scaricata il:\*\*' "$tmp_dir/out.md") \
               >/dev/null; then
        printf 'Issue #%s già aggiornata in %s\n' "$iid" "$output"
        exit 0
    fi
    if [[ "$force" -eq 0 ]]; then
        die "$output esiste già con un contenuto diverso: rilancia con --force per sovrascriverlo" 3
    fi
fi

# issues/ with its .gitignore, when the output goes there.
issues_dir="$project_root/issues"
if [[ "$(dirname "$output")" == "$issues_dir" ]]; then
    mkdir -p "$issues_dir"
    [[ -f "$issues_dir/.gitignore" ]] \
        || printf '*\n!.gitignore\n' > "$issues_dir/.gitignore"
else
    mkdir -p "$(dirname "$output")"
fi

mv "$tmp_dir/out.md" "$output"
printf 'Issue #%s scaricata da %s in %s\n' "$iid" "$tracker" "$output"
