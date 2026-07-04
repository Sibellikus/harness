#!/usr/bin/env ruby
# frozen_string_literal: true

require "optparse"
require "open3"
require "set"
require "yaml"

repo_root = File.expand_path("../../..", __dir__)
manifest_path = File.join(repo_root, "manifests", "components.yaml")

skills = Set.new
agents = Set.new
includes = Set.new
bump = "patch"
message = nil

parser = OptionParser.new do |opts|
  opts.banner = "Usage: commit_component_change.rb [--skill NAME] [--agent NAME] [--bump patch|minor|major] [--message MSG] [--include PATH]"
  opts.on("--skill NAME", "Skill name under skills/") { |value| skills.add(value) }
  opts.on("--agent NAME", "Agent name under agents/<name>.toml") { |value| agents.add(value) }
  opts.on("--bump LEVEL", "Version bump: patch, minor, or major") { |value| bump = value }
  opts.on("--message MSG", "Commit message") { |value| message = value }
  opts.on("--include PATH", "Extra path to stage with the component commit") { |value| includes.add(value) }
end

parser.parse!(ARGV)

unless %w[patch minor major].include?(bump)
  warn "Invalid bump: #{bump}"
  exit 2
end

def run_git(repo_root, *args)
  stdout, stderr, status = Open3.capture3("git", "-C", repo_root, *args)
  unless status.success?
    warn stderr
    exit status.exitstatus || 1
  end
  stdout
end

def normalize_status_path(raw_path)
  path = raw_path.strip
  path = path.split(" -> ").last if path.include?(" -> ")
  if path.start_with?('"') && path.end_with?('"')
    path = path[1..-2].gsub('\"', '"')
  end
  path
end

if skills.empty? && agents.empty?
  status = run_git(repo_root, "status", "--porcelain", "--untracked-files=all")
  status.each_line do |line|
    path = normalize_status_path(line[3..] || "")
    if path =~ %r{\Askills/([^/]+)/} && !%w[.system codex-primary-runtime].include?(Regexp.last_match(1))
      skills.add(Regexp.last_match(1))
    elsif path =~ %r{\Aagents/([^/]+)\.toml\z}
      agents.add(Regexp.last_match(1))
    end
  end
end

if skills.empty? && agents.empty?
  warn "No skill or agent changes found. Pass --skill or --agent explicitly."
  exit 2
end

unless File.file?(manifest_path)
  warn "Missing manifest: #{manifest_path}"
  exit 1
end

def bump_version(version, bump)
  major, minor, patch = version.to_s.split(".").map(&:to_i)
  case bump
  when "major"
    "#{major + 1}.0.0"
  when "minor"
    "#{major}.#{minor + 1}.0"
  else
    "#{major}.#{minor}.#{patch + 1}"
  end
end

def section_range(lines, section)
  start = lines.index { |line| line == "#{section}:\n" }
  raise "Missing section #{section}" unless start

  finish = lines[(start + 1)..]&.find_index { |line| line =~ /\A\S[^:]*:\s*\n\z/ }
  finish ? ((start + 1)..(start + finish)) : ((start + 1)..(lines.length - 1))
end

def upsert_component(lines, section, name, fields, bump)
  range = section_range(lines, section)
  component_index = range.find { |idx| lines[idx] == "  #{name}:\n" }

  if component_index
    version_index = ((component_index + 1)..range.end).find do |idx|
      break if lines[idx] =~ /\A  [^ ].*:\s*\n\z/
      lines[idx] =~ /\A    version:\s+/
    end
    raise "Missing version for #{section}.#{name}" unless version_index

    current_version = lines[version_index].split(":", 2).last.strip
    next_version = bump_version(current_version, bump)
    lines[version_index] = "    version: #{next_version}\n"
    return [current_version, next_version]
  end

  insert_at = range.end + 1
  block = ["  #{name}:\n", "    version: 0.1.0\n"]
  fields.each { |key, value| block << "    #{key}: #{value}\n" }
  lines.insert(insert_at, *block)
  ["new", "0.1.0"]
end

Dir.chdir(repo_root)

manifest = YAML.load_file(manifest_path)
raise "Invalid manifest" unless manifest.is_a?(Hash)

lines = File.readlines(manifest_path)
version_changes = []
stage_paths = Set.new(["manifests/components.yaml"])

skills.sort.each do |skill|
  path = "skills/#{skill}"
  unless Dir.exist?(File.join(repo_root, path))
    warn "Skill path does not exist: #{path}"
    exit 1
  end
  before, after = upsert_component(lines, "skills", skill, { "invocation" => "auto", "path" => path }, bump)
  version_changes << "skill #{skill}: #{before} -> #{after}"
  stage_paths.add(path)
end

agents.sort.each do |agent|
  path = "agents/#{agent}.toml"
  unless File.file?(File.join(repo_root, path))
    warn "Agent path does not exist: #{path}"
    exit 1
  end
  before, after = upsert_component(lines, "agents", agent, { "path" => path }, bump)
  version_changes << "agent #{agent}: #{before} -> #{after}"
  stage_paths.add(path)
end

File.write(manifest_path, lines.join)
YAML.load_file(manifest_path)

includes.each do |path|
  if path.start_with?("/") || path.include?("..")
    warn "Refusing unsafe include path: #{path}"
    exit 2
  end
  stage_paths.add(path)
end

message ||= if version_changes.any? { |change| change.include?("new ->") }
              "[FEATURE] Version Codex component changes"
            else
              "[CHORE] Version Codex component changes"
            end

run_git(repo_root, "add", "--", *stage_paths.to_a)

staged = run_git(repo_root, "diff", "--cached", "--name-only")
if staged.strip.empty?
  warn "No staged changes to commit."
  exit 1
end

run_git(repo_root, "commit", "-m", message)
sha = run_git(repo_root, "rev-parse", "--short", "HEAD").strip

puts "COMMIT_SHA=#{sha}"
version_changes.each { |change| puts "VERSION=#{change}" }
puts "STAGED_FILES_BEGIN"
puts staged
puts "STAGED_FILES_END"

