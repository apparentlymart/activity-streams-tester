
from os import environ
from cgi import parse_qs, escape
import urllib2
from xml.etree import ElementTree
from activitystreams.atom import make_activities_from_feed
from google.appengine.api.urlfetch import DownloadError

feed_url = ""
if "QUERY_STRING" in environ:
    query_args = parse_qs(environ["QUERY_STRING"])
    if "url" in query_args:
        feed_url = query_args["url"][0]

print "Content-type: text/html\n\n";

print "<html><head><title>Activity Streams Tester</title></head>"
print "<meta http-equiv='Content-Type' content='text/html; charset=utf-8' />"
print "<link rel='stylesheet' type='text/css' href='/static/style.css' />"
print "<body>"
print "<form action='/' method='GET'>"
print "<p><label>Feed URL: <input type='url' name='url' value=\""+escape(feed_url)+"\" size='100'></label><input type='submit'></p>"
print "</form>"

activities = None
try:
    if feed_url:
        f = urllib2.urlopen(feed_url)
        et = ElementTree.parse(f)
        activities = make_activities_from_feed(et)

except DownloadError:
    print "<p>There was an error retrieving the feed. This may be due to an incorrect URL, or it might be due to the server hosting the feed taking too long to respond.</p>"

except Exception, ex:
    print "<p>"+escape(ex.message)+"</p>"

warnings = {}

def render_activities():

    def print_object(object):
        if not object:
            return "<p>(none)</p>"

        if not object.id:
            warnings["object_no_id"] = True
        if not object.url:
            warnings["object_no_url"] = True
        if not object.object_type:
            warnings["object_no_object_type"] = True

        print "<table>"
        if object.name: print "<tr><th>Name</th><td>"+escape(object.name.encode("UTF-8"))+"</td></tr>"
        if object.id: print "<tr><th>Id</th><td>"+escape(object.id.encode("UTF-8"))+"</td></tr>"
        if object.summary: print "<tr><th>Summary</th><td>"+escape(object.summary.encode("UTF-8"))+"</td></tr>"
        if object.url: print "<tr><th>URL</th><td><a href=\""+escape(object.url.encode("UTF-8"))+"\">"+escape(object.url.encode("UTF-8"))+"</a></td></tr>"
        if object.image: print "<tr><th>Image URL</th><td><img src='"+escape(object.image.url.encode("UTF-8"))+"' width='75' align='absmiddle' /> <a href=\""+escape(object.image.url.encode("UTF-8"))+"\">"+escape(object.image.url.encode("UTF-8"))+"</a></td></tr>"
        if object.object_type:
            print "<tr><th>Object Type</th><td>"+escape(object.object_type.encode("UTF-8"))+"</td></tr>"
        else:
            print "<tr><th>Object Type</th><td>(none)</td></tr>"
        print "</table>"

    if activities:
        print "<div id='activities'>"
        print "<p>Activities in the feed <strong>"+escape(feed_url.encode("UTF-8"))+"</strong>:</p><ul class='activitylist'>"
        for activity in activities:

            if not activity.actor:
                warnings["activity_no_actor"] = True
            if not activity.object:
                warnings["activity_no_object"] = True
            if not activity.time:
                warnings["activity_no_time"] = True

            print "<li><dl>"
            if activity.time:
                print "<dt>Time</dt><dd>"
                print activity.time
                print "</dd>"
            if activity.icon_url:
                print "<dt>Icon URL</dt><dd>"
                print "<img src='"+escape(activity.icon_url)+"' width='16' height='16'> "+escape(activity.icon_url)
                print "</dd>"
            print "<dt>Actor</dt><dd>"
            print_object(activity.actor)
            print "</dd>"
            print "<dt>Verb</dt><dd>"
            if activity.verb:
                print escape(activity.verb.encode("UTF-8"))
            else:
                print "(none)"
            print "</dd>"
            print "<dt>Object</dt><dd>"
            print_object(activity.object)
            print "</dd>"
            if activity.target:
                print "<dt>Target</dt><dd>"
                print_object(activity.target)
                print "</dd>"
            print "</dl></li>"
        print "</ul>"
        print "</div>"


render_activities()

if len(warnings):
    print "<div id='warnings'>"
    print "<h2>Warnings</h2>"
    print "<p>This tool detected a few things about this feed that you may wish to fix for optimal handling by activity streams processing software:</p>"
    print "<ul>"
    if "activity_no_actor" in warnings:
        print "<li>At least one of the activities has no actor. To correct this, add a feed-level <tt>atom:author</tt> element or separate entry-level <tt>atom:author</tt> elements for each entry.</li>"
    if "activity_no_object" in warnings:
        print "<li>At least one of the activities has no object. This should actually be impossible, so it indicates a bug in this parser rather than in your feed. Whoops!</li>"
    if "activity_no_time" in warnings:
        print "<li>At least one of the activities has time associated with it. This may cause sorting or other parsing problems in consumer software. To correct this, add an entry-level <tt>atom:published</tt> element for each entry.</li>"
    if "object_no_id" in warnings:
        print "<li>The target, object or actor of at least one of the activities does not have an id. This may cause de-duping issues in consumer software. To correct this, add an <tt>atom:id</tt> element to the element that represents each object.</li>"
    if "object_no_url" in warnings:
        print "<li>The target, object or actor of at least one of the activities does not have a URL associated with it. A permalink URL makes an object more useful.</li>"
    if "object_no_object_types" in warnings:
        print "<li>The target, object or actor of at least one of the activities does not have any explicit object types. Consumers can handle an object better if it's annotated with an appropriate object type using the <tt>activity:object-type</tt> element.</li>"
    print "</ul>"
    print "<p>Please note that this tool is not a validator and so fixing the above items does not necessarily mean that your feed is valid or useful.</p>"
    print "</div>"

print "</body></html>"
