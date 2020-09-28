\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{finalreport}[Internship Summary Report]
\LoadClass[a4paper]{article}

\RequirePackage{graphicx}

\RequirePackage{geometry}
\geometry{margin=0.75in}

\RequirePackage{amsmath, amsfonts, amssymb}

\RequirePackage[hidelinks]{hyperref}
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=cyan
}

\RequirePackage[T1]{fontenc}
\RequirePackage[acronyms]{glossaries}
\RequirePackage[style=phys, backend=biber, defernumbers=true]{biblatex}

%%% Title page
\RequirePackage[]{titling}
% \setlength{\droptitle}{-10em}
\pretitle{\begin{center} \Huge}
\posttitle{
\\[\bigskipamount]
\thedate
\end{center}
\vspace{20em}
}

\preauthor{\begin{center} \LARGE}
\postauthor{\\
\vspace{3em}
\includegraphics[scale=0.3]{Maniac_Logo_extended.png}
\\[\bigskipamount]
Enrico Fermi Institute \\
University of Chicago \\
\end{center}
}

% Hide date at bottom
\predate{\phantom}
\postdate{}

% \RequirePackage[]{authblk}
% \renewcommand\Authfont{\fontsize{18}{21.6}\selectfont}


%%% Page headers
\RequirePackage{fancyhdr}
\pagestyle{fancy}
\setlength\headheight{30pt}
\lhead{Modeling Network Disruptions $\cdotp$\space\theauthor\space$\cdotp$ \thedate}
\rhead{\includegraphics[scale=.2]{Maniac_Logo_extended.png}}


%%% Date calculations
\RequirePackage[calc,useregional,english]{datetime2}
\newcount\myct
% \newcount\datecount
\DTMnewdatestyle{weekdayformat}{%
    \renewcommand{\DTMdisplaydate}[4]{%
        \DTMweekdayname{##4},\space% short weekday,
        \DTMmonthname{##2}\nobreakspace%  (full) Month
        \number##3\space% day
        % \number##1% year
    }%
    \renewcommand{\DTMDisplaydate}{\DTMdisplaydate}%
}
\newcommand{\weekday}[1]{%
    \DTMsaveddateoffsettojulianday{startdate}{#1}{\myct}%
    \DTMsavejulianday{mydate}{\myct}%
    \DTMsetdatestyle{weekdayformat}%
    \DTMusedate{mydate}%
}
\DTMnewdatestyle{enddateformat}{%
    \renewcommand{\DTMdisplaydate}[4]{%
        % \DTMweekdayname{##4},\space% short weekday,
        \DTMmonthname{##2}\nobreakspace%  (full) Month
        \number##3,\space% day
        \number##1% year
    }%
    \renewcommand{\DTMDisplaydate}{\DTMdisplaydate}%
}
\newcommand{\reportenddate}{%
    \DTMsaveddateoffsettojulianday{startdate}{4}{\myct}%
    \DTMsavejulianday{mydate}{\myct}%
    \DTMsetdatestyle{enddateformat}%
    \DTMusedate{mydate}%
}


%%% Section headers
\RequirePackage{titlesec}

\titleformat{\section}
    {\LARGE}
    {}{0em}
    {}
    [\titlerule]

\titleformat{\subsection}
    {\Large}
    {}{0em}
    {}