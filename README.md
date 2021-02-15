# philstransactions
This is a program that I run to get email notifications about Phillies transactions; it's an easier way to check the Transactions list on the Phillies website.

You'll need a config file to send emails/connect to a database.  I used a MySQL database with 3 columns: primary key "playerid", "name", and "frequency".

If you change the URL in the create_url() function it will work for any MLB team.
