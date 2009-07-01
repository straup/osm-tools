#!/usr/bin/env perl
use strict;

use Getopt::Std;
use FileHandle;

use HTML::TableExtract;
use LWP::Simple;
use JSON::Any;

{
        &main();
        exit;
}

sub main {

        my %opts = ();
        getopts('o:d', \%opts);

        my $url = "http://wiki.openstreetmap.org/wiki/Map_Features";
        my $html = get($url);

        my $te = HTML::TableExtract->new(headers=>['Key', 'Value', 'Comment']);
        $te->parse($html);

        my @features = ();

        foreach my $table ($te->tables()){
                foreach my $row ($table->rows()){

                        my ($pred, $value, $desc) = @{$row};

                        if (! $value){
                                next;
                        }

                        $pred = trim($pred);
                        $value = trim($value);


                        if ($value =~ /\s/){
                                $value = "\"$value\"";
                        }

                        my %data = ('namespace' => 'osm', 'predicate' => $pred, 'value' => $value,);

                        if ($opts{'d'}){
                                $desc = trim($desc);
                                $data{'description'} = "\"$desc\"";
                        }

                        push @features, \%data;
                }
        }

        my $fh = FileHandle->new();

        if (! $fh->open(">$opts{'o'}")){
                warn "failed to open '" . $opts{'o'} . "' for writing, $!";
                return 0;
        }

        binmode $fh, ":utf8";

        # work out other formats here...

        my $json = JSON::Any->new();
        $fh->print($json->encode({'features' => \@features}));

        $fh->close();
        return 1;
}

sub trim {
        my $str = shift;
        $str =~ s/^\s+//;
        $str =~ s/\s+$//;
        $str =~ s/\n//gm;
        return $str;
}

=head1 NAME

mapfeature_extractor.pl - A CLI tool for generating a machine (tag) readable dump of the OSM Map Features wiki page

=head1 SYNOPSIS

 $> mapfeature_extractor.pl -o /path/to/outfile

=head1 DESCRIPTION

mapfeature_extractor.pl is a command-line tool for generating a machine (tag) readable (JSON) dump
of the OSM Map Features wiki page.

=head1 OPTIONS

=over 4

=item * B<o> (outfile)

The path to a file where the data should be written.

Required.

=item * B<d> (description)

Include OSM descriptions with each item.

Optional.

=back

=head1 TO DO

=over 4

=item * Generate output formats other than JSON

=item * Include a "pretty print" option

=item * Be smart about generating multiple entries for features whose values are "foo / bar / baz"

=item * Uh...stuff?

=back

L<http://wiki.openstreetmap.org/wiki/Map_Features>

=head1 AUTHOR

Aaron Straup Cope.

=head1 LICENSE

Copyright (c) 2009 Aaron Straup Cope. All rights reserved.

This is free software, you may use it and distribute it under the same
terms as Perl itself.

=cut

# -*-cperl-*-
