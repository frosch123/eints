%rebase('main_template', title='Web Translator - {}'.format(pmd.human_name))
%from webtranslate import utils, data
<h1>{{pmd.human_name}}</h1>
<hr />
<h2 class="eint-heading-icon eint-icon-drawer-open">Project Overview</h2>
% if base_lng is None:
    <p class="alert alert-info"><strong>To get started, please <a href="/upload/{{pmd.name}}">upload a lang file</a> to use as base language.</strong></p>
% else:
    <br />
    <br />
    <table class="table table-condensed table-striped table-hover">
        <thead>
            <tr>
                <th colspan="3">Languages ({{len(pmd.pdata.languages)}})</th>
                <th colspan="2" style="text-align:center;"><i class="icon-cog"></i> Actions</th>
                <th colspan="{{len(data.STATE_DISPLAY)}}" style="text-align:center;">Strings ({{len(base_lng.changes)}})</th>
            </tr>
            <tr>
                <th colspan="5"></th>
                % for s in reversed(data.STATE_DISPLAY):
                    <th class="number">{{s.name}}</th>
                % end
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><i class="icon-leaf"></i></td>
                <td><strong><a href="/translation/{{pmd.name}}/{{base_lng.name}}">{{base_lng.name}}</a></strong></td>
                <td><strong><a href="/translation/{{pmd.name}}/{{base_lng.name}}">{{base_lng.info.name}}</a></strong></td>
                <td><strong>(Base Language)</strong></td>
                <td><a class="pull-right" href="/download/{{pmd.name}}/{{base_lng.name}}"><i class="icon-download"></i> Download</a></td>
                % for s in reversed(data.STATE_DISPLAY):
                    % if s.baselng:
                        <td class="number"><strong>{{bcounts[s.code]}}</strong></td>
                    % else:
                        <td class="number"><strong>-</strong></td>
                    % end
                % end
            </tr>
        % if len(transl) == 0:
            <tr>
                <td colspan="{{5 + len(data.STATE_DISPLAY)}}" class="alert alert-info">To get started with translation, upload a language file</td>
            </tr>
        % else:
            % for lng, counts in transl:
                <tr>
                    <td>
                        % if not utils.lang_needs_fixing(counts):
                            <i class="icon-ok-circle"></i>
                        % else:
                            <i class="icon-exclamation-sign"></i>
                        % end
                    </td>
                    <td><a href="/translation/{{pmd.name}}/{{lng.name}}">{{lng.name}}</a></td>
                    <td><a href="/translation/{{pmd.name}}/{{lng.name}}">{{lng.info.name}}</a></td>
                    % if utils.lang_needs_fixing(counts):
                        <td><a href="/fix/{{pmd.name}}/{{lng.name}}">Start Fixing</a></td>
                    % else:
                        <td>Done!</td>
                    % end
                    <td><a class="pull-right" href="/download/{{pmd.name}}/{{lng.name}}"><i class="icon-download"></i> Download</a></td>
                    % for s in reversed(data.STATE_DISPLAY):
                        <td class="number">{{counts[s.code]}}</td>
                    % end
                </tr>
            % end
        % end
        </tbody>
    </table>
    <br />
    <dl class="dl-horizontal">
        % for s in reversed(data.STATE_DISPLAY):
            <dt>{{s.name}}</dt>
            <dd>{{s.description}}</dd>
        % end
    </dl>
%end
