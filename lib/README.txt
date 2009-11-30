This folder began as a place to store svnant jar files.  It may evolve into
something more over time.

It's probably better to keep these files here (in a buildtools lib dir) than
embedded in %ANT_HOME%\etc or somewhere like that, because it simplifies
things for the developers as well.  There was an issue earlier where the svn
taskdef was not found, and the build failed because of it.  As far as
possible, I'm trying to remove those.

The svnant jars were compiled from source.  There's a nice HOWTO called
"Integrating Apache Ant and Subversion" at the buildmeister site.

[http://www.buildmeister.com/viewarticle.php?id=24]

----
At the moment, there are four jars in the lib/ dir:

C:\Source\buildtools\branches\9.1\gold>ls lib
README.txt  svnant.jar  svnClientAdapter.jar  svnjavahl.jar  svnkit.jar

Maybe a fifth (ganymed.jar) should be here as well.  Not sure yet.

Late note: ganymed.jar is only needed if we're using SSH, which we're not.

----
Late note: the other jar files were all updated to 1.2.0-RC1 on 11/19/2008 to
work with Subversion 1.5.

----
Get SVNAnt here: http://subclipse.tigris.org/svnant.html

----
Current svnant version: 1.2.1
-timc 5/1/2009

