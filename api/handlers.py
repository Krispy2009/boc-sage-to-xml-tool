async def root():
    return """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>

            <h1>Sage report to BoC XML conversion tool</h1>
            <form action=/>
                <input type="file" id="myFile" name="filename">
                <input type="submit">
            </form>
        </body>
    </html>
    """
