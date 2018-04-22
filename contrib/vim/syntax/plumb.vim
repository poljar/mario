" Vim syntax file
" Language: Mario rules
" Maintainers: Damir Jelić, Denis Kasak
" Latest Revision: 26 March 2015

if exists('b:current_syntax')
  finish
endif

" Keywords
syn region marioRuleName start="^\s*\[" end="\]"
syn keyword marioMatchObjects kind data arg nextgroup=marioMatchVerbs
syn keyword marioKinds raw url
syn keyword marioMatchVerbs is istype matches rewrite
syn keyword marioActionObjects plumb nextgroup=marioActionVerbs
syn keyword marioActionVerbs download notify run
syn region marioVariable start="{" end="}"

syn match marioComment "#.*$"

hi def link marioComment       Comment
hi def link marioRuleName      Title
hi def link marioVariable      Type

hi def link marioMatchObjects  Keyword
hi def link marioMatchVerbs    Function

hi def link marioActionObjects Keyword
hi def link marioActionVerbs   Function

set commentstring=#%s
set comments=b:#

let b:current_syntax = 'plumb'
