%from urllib.parse import quote
%from webtranslate.bottle import url, request
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <title>{{title or 'No title'}}</title>
    <link type="text/css" href="{{ url('static', path='css/bootstrap.min.css') }}" rel="stylesheet">
    <!-- load order is significant for css, our over-rides on bootstrap must load after bootstrap -->
    <link type="text/css" href="{{ url('static', path='css/style.css') }}" rel="stylesheet">
    <script type="text/javascript" src="{{ url('static', path='js/jquery-1.9.1.min.js') }}"></script>
    <script type="text/javascript" src="{{ url('static', path='js/bootstrap.min.js') }}"></script>
    <script type="text/javascript" src="{{ url('static', path='js/bootstrap-filestyle-0.1.0.js') }}"></script>
    <script type="text/javascript">
        $(document).ready(function() {
            $(":file").filestyle({classButton:"btn-info"});
        });
    </script>
</head>
<body>
    <div class="container">
        <div class="navbar eint-navbar">
            <div class="navbar-inner">
                <ul class="nav">
                    <li><a href="/"><i class="icon-home"></i> Home</a></li>
                    <li><a href="/project/openttd-master"><i class="icon-list-alt"></i> OpenTTD</a></li>
                </ul>
                <ul class="nav pull-right">
                    <li><a target="_blank" href="http://bundles.openttdcoop.org/eints/nightlies/LATEST/docs/usage.html"><i class="icon-book"></i> Manual</a></li>
                    %if userauth.is_auth:
                        <li><a href="/userprofile"><i class="icon-user"></i> Profile ({{ userauth.name }})</a></li>
                        <li><a href="/logout"><i class="icon-user"></i> Logout</a></li>
                    %else:
                        <li><a href="/login?redirect={{ quote(request.path) }}"><i class="icon-user"></i> Login</a></li>
                    %end
                </ul>
            </div>
        </div>

        %for message in messages:
            <div id="message-slot" class="alert {{message['class']}}">
                {{message['content']}}
            </div>
        %end
        <!-- content from calling template -->
        {{!base}}

        <div class="footer">
            <a href="http://dev.openttdcoop.org/projects/eints">Web Translator</a> from <a href="http://dev.openttdcoop.org">#openttdcoop</a>
        </div>
    </div>
</body>
</html>
